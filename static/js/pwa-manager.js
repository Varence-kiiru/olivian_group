// Olivian Group - PWA Manager
class PWAManager {
    constructor() {
        this.deferredPrompt = null;
        this.serviceWorkerRegistered = false;
        this.isOnline = navigator.onLine;
        this.init();
    }

    async init() {
        // Register service worker
        await this.registerServiceWorker();

        // Initialize PWA features
        this.initInstallPrompt();
        this.initNetworkStatus();
        this.initPeriodicSync();
        this.initBackgroundSync();

        console.log('✅ PWA Manager initialized');
    }

    // Service Worker Registration
    async registerServiceWorker() {
        if ('serviceWorker' in navigator) {
            try {
                // Check if service worker is already registered
                const registration = await navigator.serviceWorker.getRegistration();
                if (registration) {
                    console.log('[PWA] Service worker already registered');
                    this.serviceWorkerRegistered = true;
                    this.setupServiceWorkerListeners(registration);
                    return;
                }

                // Register new service worker from correct path with allowed scope
                const newRegistration = await navigator.serviceWorker.register('/sw.js', {
                    scope: '/'
                });

                console.log('[PWA] Service worker registered:', newRegistration.scope);
                this.serviceWorkerRegistered = true;

                // Handle updates
                if (newRegistration.waiting) {
                    this.handleUpdateAvailable(newRegistration.waiting);
                }

                newRegistration.addEventListener('updatefound', () => {
                    const newWorker = newRegistration.installing;
                    newWorker.addEventListener('statechange', () => {
                        if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                            this.handleUpdateAvailable(newWorker);
                        }
                    });
                });

                this.setupServiceWorkerListeners(newRegistration);

            } catch (error) {
                console.error('[PWA] Service worker registration failed:', error);
            }
        } else {
            console.warn('[PWA] Service workers not supported');
        }
    }

    setupServiceWorkerListeners(registration) {
        // Message handling from service worker
        navigator.serviceWorker.addEventListener('message', (event) => {
            this.handleServiceWorkerMessage(event);
        });

        // Controller change (new service worker activated)
        navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('[PWA] Service worker controller changed, reloading page');
            window.location.reload();
        });
    }

    handleUpdateAvailable(worker) {
        // Create update notification
        const updateBanner = document.createElement('div');
        updateBanner.id = 'pwa-update-banner';
        updateBanner.innerHTML = `
            <div class="update-banner-content">
                <i class="fas fa-download"></i>
                <span>New version available!</span>
                <button id="update-app-btn" class="btn btn-sm btn-primary">Update Now</button>
                <button id="dismiss-update-btn" class="btn btn-sm btn-link">Later</button>
            </div>
        `;

        // Style the update banner
        updateBanner.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #38b6ff, #2c8fd6);
            color: white;
            padding: 0.75rem;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            z-index: 10000;
            font-size: 0.9rem;
            display: flex;
            align-items: center;
            justify-content: center;
        `;

        const bannerContent = updateBanner.querySelector('.update-banner-content');
        bannerContent.style.cssText = `
            display: flex;
            align-items: center;
            justify-content: center;
            gap: 0.75rem;
        `;

        document.body.appendChild(updateBanner);

        // Handle update button click
        document.getElementById('update-app-btn').addEventListener('click', () => {
            worker.postMessage({ type: 'SKIP_WAITING' });
            updateBanner.remove();
        });

        // Handle dismiss button click
        document.getElementById('dismiss-update-btn').addEventListener('click', () => {
            updateBanner.remove();
        });

        // Auto-remove after 30 seconds
        setTimeout(() => {
            if (updateBanner.parentNode) {
                updateBanner.remove();
            }
        }, 30000);
    }

    handleServiceWorkerMessage(event) {
        const { data } = event;
        console.log('[PWA] Message from service worker:', data);

        switch (data.type) {
            case 'SYNC_COMPLETED':
                this.showToast('Changes synced successfully!', 'success');
                break;
            case 'SYNC_FAILED':
                this.showToast('Sync failed, will retry automatically', 'warning');
                break;
            case 'OFFLINE_READY':
                this.showToast('App ready for offline use!', 'info');
                break;
        }
    }

    // Install Prompt Management
    initInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (e) => {
            console.log('[PWA] Install prompt available');
            e.preventDefault();
            this.deferredPrompt = e;
            this.showInstallBanner();
        });

        // Handle successful installation
        window.addEventListener('appinstalled', (e) => {
            console.log('[PWA] App was installed');
            this.hideInstallBanner();
            this.showToast('App installed successfully!', 'success');
            this.deferredPrompt = null;
        });
    }

    showInstallBanner() {
        // Check if already shown recently
        const lastShown = localStorage.getItem('pwa-install-last-shown');
        if (lastShown && Date.now() - parseInt(lastShown) < 24 * 60 * 60 * 1000) {
            return; // Don't show again within 24 hours
        }

        const installBanner = document.createElement('div');
        installBanner.id = 'pwa-install-banner';
        installBanner.innerHTML = `
            <div class="install-banner-content">
                <i class="fas fa-mobile-alt"></i>
                <div class="install-text">
                    <strong>Get the Olivian App!</strong>
                    <span>Install for faster access and offline features</span>
                </div>
                <div class="install-actions">
                    <button id="install-app-btn" class="btn btn-sm btn-success">
                        <i class="fas fa-download"></i> Install
                    </button>
                    <button id="dismiss-install-btn" class="btn btn-sm btn-link">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            </div>
        `;

        installBanner.style.cssText = `
            position: fixed;
            bottom: 20px;
            left: 20px;
            right: 20px;
            background: white;
            border-radius: 12px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
            padding: 1rem;
            z-index: 10000;
            border: 1px solid #e9ecef;
            max-width: 400px;
            margin: 0 auto;
            display: none;
        `;

        const bannerContent = installBanner.querySelector('.install-banner-content');
        bannerContent.style.cssText = `
            display: flex;
            align-items: center;
            gap: 0.75rem;
        `;

        const installText = bannerContent.querySelector('.install-text');
        installText.style.cssText = `
            flex: 1;
            font-size: 0.9rem;
        `;

        const installActions = bannerContent.querySelector('.install-actions');
        installActions.style.cssText = `
            display: flex;
            flex-direction: column;
            gap: 0.25rem;
        `;

        document.body.appendChild(installBanner);

        // Animate in
        setTimeout(() => {
            installBanner.style.display = 'block';
            installBanner.style.animation = 'slideInUp 0.3s ease-out';
        }, 2000); // Show after 2 seconds

        // Handle install button click
        document.getElementById('install-app-btn').addEventListener('click', () => {
            this.installPWA();
            installBanner.remove();
        });

        // Handle dismiss button click
        document.getElementById('dismiss-install-btn').addEventListener('click', () => {
            installBanner.remove();
            localStorage.setItem('pwa-install-dismissed', Date.now().toString());
        });
    }

    hideInstallBanner() {
        const banner = document.getElementById('pwa-install-banner');
        if (banner) {
            banner.remove();
        }
    }

    async installPWA() {
        if (!this.deferredPrompt) {
            this.showToast('Installation not available', 'info');
            return;
        }

        try {
            const result = await this.deferredPrompt.prompt();
            console.log('[PWA] Install prompt result:', result);

            if (result.outcome === 'accepted') {
                console.log('[PWA] User accepted installation');
            } else {
                console.log('[PWA] User dismissed installation');
            }

            this.deferredPrompt = null;
        } catch (error) {
            console.error('[PWA] Installation failed:', error);
            this.showToast('Installation failed', 'error');
        }
    }

    // Network Status Management
    initNetworkStatus() {
        window.addEventListener('online', () => {
            console.log('[PWA] Network back online');
            this.isOnline = true;
            this.showToast('Back online!', 'success');
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            console.log('[PWA] Network went offline');
            this.isOnline = false;
            this.showToast('You\'re offline', 'warning');
        });

        // Create connection indicator
        this.createConnectionIndicator();
    }

    createConnectionIndicator() {
        const indicator = document.createElement('div');
        indicator.id = 'connection-indicator';
        indicator.innerHTML = `
            <i class="fas fa-wifi"></i>
            <span>Online</span>
        `;

        indicator.style.cssText = `
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: rgba(40, 167, 69, 0.9);
            color: white;
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            opacity: 0;
            transition: opacity 0.3s ease;
            z-index: 1000;
            backdrop-filter: blur(10px);
            pointer-events: none;
        `;

        document.body.appendChild(indicator);

        // Show indicator briefly when connection changes
        const showIndicator = (online) => {
            const indicator = document.getElementById('connection-indicator');
            if (online) {
                indicator.style.background = 'rgba(40, 167, 69, 0.9)';
                indicator.querySelector('i').className = 'fas fa-wifi';
                indicator.querySelector('span').textContent = 'Online';
            } else {
                indicator.style.background = 'rgba(220, 53, 69, 0.9)';
                indicator.querySelector('i').className = 'fas fa-wifi-slash';
                indicator.querySelector('span').textContent = 'Offline';
            }

            indicator.style.opacity = '1';
            setTimeout(() => {
                indicator.style.opacity = '0';
            }, 3000);
        };

        window.addEventListener('online', () => showIndicator(true));
        window.addEventListener('offline', () => showIndicator(false));
    }

    // Periodic Background Sync
    initPeriodicSync() {
        if ('serviceWorker' in navigator && 'periodicSync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then((registration) => {
                // Register periodic sync for notifications
                registration.periodicSync.register('update-notifications', {
                    minInterval: 15 * 60 * 1000, // 15 minutes minimum
                }).catch((error) => {
                    console.log('[PWA] Periodic sync registration failed:', error);
                });
            });
        }
    }

    // Background Sync for Forms and Chat
    initBackgroundSync() {
        if ('serviceWorker' in navigator && 'sync' in window.ServiceWorkerRegistration.prototype) {
            navigator.serviceWorker.ready.then((registration) => {
                // Register background sync tags
                this.registerSyncTag(registration, 'background-sync-chat');
                this.registerSyncTag(registration, 'background-sync-forms');
            });
        }
    }

    registerSyncTag(registration, tag) {
        registration.sync.register(tag).catch((error) => {
            console.log(`[PWA] Background sync registration failed for ${tag}:`, error);
        });
    }

    // Sync pending data when coming online
    async syncPendingData() {
        if (!this.serviceWorkerRegistered) return;

        try {
            // Trigger background sync
            const registration = await navigator.serviceWorker.ready;

            await registration.sync.register('background-sync-chat');
            await registration.sync.register('background-sync-forms');

            console.log('[PWA] Background sync triggered');
        } catch (error) {
            console.error('[PWA] Background sync failed:', error);
        }
    }

    // Utility methods
    showToast(message, type = 'info') {
        // Check if toast container exists
        let toastContainer = document.querySelector('.toast-container');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '1060';
            document.body.appendChild(toastContainer);
        }

        const toast = document.createElement('div');
        toast.className = `toast align-items-center text-white bg-${type} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">${message}</div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        toastContainer.appendChild(toast);

        // Initialize Bootstrap toast
        if (typeof bootstrap !== 'undefined') {
            const bsToast = new bootstrap.Toast(toast, {
                autohide: true,
                delay: 3000
            });
            bsToast.show();
        } else {
            // Fallback if Bootstrap not loaded
            setTimeout(() => {
                if (toast.parentNode) {
                    toast.remove();
                }
            }, 3000);
        }

        // Remove toast after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Static utilities
    static isPWA() {
        return window.matchMedia('(display-mode: standalone)').matches ||
               window.navigator.standalone === true;
    }

    static isOnline() {
        return navigator.onLine;
    }

    static getCacheSize() {
        return navigator.storage && navigator.storage.estimate ?
            navigator.storage.estimate().then(estimate => ({
                used: estimate.usage || 0,
                available: estimate.quota || 0
            })) : Promise.resolve({ used: 0, available: 0 });
    }

    static async clearCache() {
        const cacheNames = await caches.keys();
        await Promise.all(
            cacheNames.map(cacheName => caches.delete(cacheName))
        );
        console.log('[PWA] Cache cleared');
    }
}

// Initialize PWA Manager when page loads
document.addEventListener('DOMContentLoaded', () => {
    if ('serviceWorker' in navigator) {
        window.pwaManager = new PWAManager();
    }
});

// Export for global access
window.PWAManager = PWAManager;
