// Olivian Group - Main JavaScript

// Utility functions
const OlivianSolar = {
    // Initialize common functionality
    init: function() {
        this.initTooltips();
        this.initAlerts();
        this.initAnimations();
        this.initChatNotifications();
        this.initAccessibility();
    },

    // Initialize Bootstrap tooltips
    initTooltips: function() {
        if (typeof bootstrap !== 'undefined') {
            const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
            tooltipTriggerList.map(function (tooltipTriggerEl) {
                return new bootstrap.Tooltip(tooltipTriggerEl);
            });
        }
    },

    // Auto-hide alerts
    initAlerts: function() {
        const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
        alerts.forEach(alert => {
            const delay = alert.dataset.autoDismiss || 5000;
            setTimeout(() => {
                if (typeof bootstrap !== 'undefined') {
                    const bsAlert = new bootstrap.Alert(alert);
                    bsAlert.close();
                } else {
                    alert.style.display = 'none';
                }
            }, delay);
        });
    },

    // Initialize animations
    initAnimations: function() {
        // Fade in animation for cards
        const cards = document.querySelectorAll('.card, .dashboard-card');
        cards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(20px)';
            setTimeout(() => {
                card.style.transition = 'all 0.5s ease';
                card.style.opacity = '1';
                card.style.transform = 'translateY(0)';
            }, index * 100);
        });
    },

    // Format currency
    formatCurrency: function(amount, currency = 'KES') {
        return new Intl.NumberFormat('en-KE', {
            style: 'currency',
            currency: currency,
            minimumFractionDigits: 2
        }).format(amount);
    },

    // Show loading state
    showLoading: function(element) {
        if (element) {
            element.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
            element.disabled = true;
        }
    },

    // Hide loading state
    hideLoading: function(element, originalText) {
        if (element) {
            element.innerHTML = originalText;
            element.disabled = false;
        }
    },

    // Global Chat Notification System
    chatNotification: {
        lastMessageId: 0,
        currentRoomName: null,
        notificationSound: null,
        pollInterval: null,
        currentUserId: null,

        init: function() {
            this.currentUserId = window.user_id || document.querySelector('meta[name="user-id"]')?.content;
            if (!this.currentUserId) return;

            // Get current room name from URL if in chat room
            const urlPath = window.location.pathname;
            const roomMatch = urlPath.match(/^\/chat\/room\/([^\/]+)\//);
            if (roomMatch) {
                this.currentRoomName = roomMatch[1];
            }

            this.initializeLastMessageId();
            this.startSmartPolling();
            this.requestNotificationPermission();
        },

        initializeLastMessageId: function() {
            // If in a chat room, use the room's last message ID
            if (window.location.pathname.includes('/chat/room/')) {
                const messageItems = document.querySelectorAll('.message-item[data-message-id]');
                if (messageItems.length > 0) {
                    const lastItem = messageItems[messageItems.length - 1];
                    this.lastMessageId = parseInt(lastItem.dataset.messageId) || 0;
                }
            } else {
                // If not in chat room, just start from 0 for global notifications
                this.lastMessageId = 0;
            }
        },

        startSmartPolling: function() {
            // Register with the Smart Polling Manager
            if (window.SmartPollingManager) {
                window.SmartPollingManager.register('global_chat_notifications', {
                    url: `/chat/api/messages/global/?last_id=${this.lastMessageId}`,
                    method: 'GET',
                    interval: 5000,        // Base interval: 5 seconds (matching old behavior)
                    maxInterval: 30000,    // Max 30 seconds during inactivity
                    successCallback: (data) => this.handlePollResponse(data),
                    errorCallback: (error) => this.handlePollError(error),
                    dataCallback: (data) => this.processResponseData(data),
                    pauseOnBlur: true,     // Pause when tab not visible
                    pauseOffline: true,    // Pause when offline
                    enabled: true
                });
            } else {
                // Fallback to old polling if SmartPollingManager not available
                console.warn('SmartPollingManager not found, falling back to legacy polling');
                this.startLegacyPolling();
            }
        },

        startLegacyPolling: function() {
            // Fallback: original fixed-interval polling
            this.pollInterval = setInterval(() => {
                this.pollForNewMessages();
            }, 5000);
        },

        pollForNewMessages: function() {
            // Legacy polling method (kept for fallback)
            fetch(`/chat/api/messages/global/?last_id=${this.lastMessageId}`, {
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                },
            })
            .then(response => response.json())
            .then(data => {
                if (data.messages && data.messages.length > 0) {
                    data.messages.forEach(message => {
                        if (message.id > this.lastMessageId) {
                            this.handleNewMessage(message);
                            this.lastMessageId = Math.max(this.lastMessageId, message.id);
                        }
                    });

                    this.updateChatIconBadge(data.unread_count);
                }
            })
            .catch(error => {
                console.log('Global chat poll error:', error);
            });
        },

        handlePollResponse: function(data) {
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(message => {
                    if (message.id > this.lastMessageId) {
                        this.handleNewMessage(message);
                        this.lastMessageId = Math.max(this.lastMessageId, message.id);
                    }
                });

                this.updateChatIconBadge(data.unread_count);

                // Reset polling interval when new messages arrive
                if (window.SmartPollingManager) {
                    window.SmartPollingManager.resetInterval('global_chat_notifications');
                }
            }
        },

        processResponseData: function(data) {
            // Return true if there's new data (messages or unread count changes)
            return (data.messages && data.messages.length > 0) ||
                   (data.unread_count && data.unread_count > 0);
        },

        handlePollError: function(error) {
            console.log('Smart polling error for global notifications:', error);
        },

        handleNewMessage: function(message) {
            // Only notify if user is not in the room where the message was sent
            const messageRoomName = message.room_name;
            const isInCurrentRoom = this.currentRoomName === messageRoomName;

            if (!isInCurrentRoom) {
                // Play notification sound
                this.playNotificationSound();

                // Show browser notification if permitted
                this.showBrowserNotification(message);

                // Show message popup notification
                this.showMessagePopup(message);
            }

            // Update floating chat icon badge
            this.updateChatIconBadge();
        },

        playNotificationSound: function() {
            try {
                this.notificationSound = new Audio('/static/sounds/alert.mp3');
                this.notificationSound.volume = 0.5;
                this.notificationSound.play().catch(e => {
                    console.log('Notification sound failed, trying fallback:', e);
                    this.playFallbackSound();
                });
            } catch (error) {
                console.log('Audio error:', error);
                this.playFallbackSound();
            }
        },

        playFallbackSound: function() {
            try {
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();

                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);

                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
                oscillator.frequency.setValueAtTime(400, audioContext.currentTime + 0.2);

                gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);

                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
            } catch (error) {
                console.log('Fallback audio also failed:', error);
            }
        },

        showBrowserNotification: function(message) {
            if ('Notification' in window && Notification.permission === 'granted') {
                const notification = new Notification(`💬 ${message.room.display_name || message.room_name}`, {
                    body: `${message.author_full_name}: ${message.content.substring(0, 100)}${message.content.length > 100 ? '...' : ''}`,
                    icon: '/static/images/logo.png',
                    tag: `chat-${message.room_name}`,
                    requireInteraction: false
                });

                notification.onclick = function() {
                    window.focus();
                    window.location.href = `/chat/room/${message.room_name}/`;
                    notification.close();
                };

                // Auto-close after 5 seconds
                setTimeout(() => notification.close(), 5000);
            }
        },

        showMessagePopup: function(message) {
            const notificationEl = document.createElement('div');
            notificationEl.className = 'message-notification';
            notificationEl.innerHTML = `
                <div class="notification-content">
                    <div class="notification-icon">
                        <i class="fas fa-comments"></i>
                    </div>
                    <div class="notification-text">
                        <strong>New Message in ${message.room.display_name || message.room_name}</strong>
                        <span class="notification-sender">${message.author_full_name}</span>
                        <span class="notification-preview">${message.content.substring(0, 100)}${message.content.length > 100 ? '...' : ''}</span>
                    </div>
                    <button class="notification-close" onclick="this.parentElement.parentElement.remove()">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
            `;

            // Make it clickable to go to chat room
            notificationEl.addEventListener('click', (e) => {
                if (!e.target.closest('.notification-close')) {
                    window.location.href = `/chat/room/${message.room_name}/`;
                }
            });

            document.body.appendChild(notificationEl);

            // Add show class for animation
            setTimeout(() => {
                notificationEl.classList.add('show');
            }, 100);

            // Auto-dismiss after 8 seconds
            setTimeout(() => {
                if (notificationEl.parentElement) {
                    notificationEl.classList.remove('show');
                    setTimeout(() => {
                        if (notificationEl.parentElement) {
                            notificationEl.remove();
                        }
                    }, 300);
                }
            }, 8000);
        },

        updateChatIconBadge: function(unreadCount = null) {
            const badgeEl = document.getElementById('chatNotificationBadge');
            if (!badgeEl) return;

            if (unreadCount === null) {
                // Fetch unread count
                fetch('/chat/api/unread-count/', {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                })
                .then(response => response.json())
                .then(data => {
                    this.updateBadgeDisplay(data.unread_count);
                })
                .catch(error => console.log('Error fetching unread count:', error));
            } else {
                this.updateBadgeDisplay(unreadCount);
            }
        },

        updateBadgeDisplay: function(count) {
            const badgeEl = document.getElementById('chatNotificationBadge');
            if (!badgeEl) return;

            if (count > 0) {
                badgeEl.textContent = count > 99 ? '99+' : count;
                badgeEl.style.display = 'flex';
            } else {
                badgeEl.style.display = 'none';
            }
        },

        requestNotificationPermission: function() {
            if ('Notification' in window && Notification.permission === 'default') {
                console.log('Browser notification permission pending - will request on first user interaction');

                // Request permission on first user click
                const requestPermissionHandler = async () => {
                    try {
                        const permission = await Notification.requestPermission();
                        console.log('Notification permission:', permission);

                        if (permission === 'granted') {
                            console.log('✅ Notifications enabled successfully!');
                        } else {
                            console.log('❌ Notification permission denied');
                        }
                    } catch (error) {
                        console.error('Error requesting notification permission:', error);
                    }

                    // Remove the listener after first request
                    document.removeEventListener('click', requestPermissionHandler);
                };

                // Add listener for first user interaction
                document.addEventListener('click', requestPermissionHandler, { once: true });
            }
        },

        cleanup: function() {
            if (this.pollInterval) {
                clearInterval(this.pollInterval);
            }
        }
    },

    // Initialize global chat notifications
    initChatNotifications: function() {
        this.chatNotification.init();
    },

    // Enhanced Accessibility Features
    accessibility: {
        init: function() {
            this.initKeyboardNavigation();
            this.initScreenReaderEnhancements();
            this.initFocusManagement();
            this.initReducedMotion();
        },

        initKeyboardNavigation: function() {
            // Enhanced keyboard navigation for mobile
            document.addEventListener('keydown', function(e) {
                // Escape key handling
                if (e.key === 'Escape') {
                    // Close mobile sidebar
                    if (window.innerWidth <= 768) {
                        const sidebar = document.getElementById('sidebar');
                        sidebar.classList.remove('show');
                    }

                    // Close dropdowns
                    const dropdowns = document.querySelectorAll('.dropdown-menu.show');
                    dropdowns.forEach(dropdown => {
                        const bsDropdown = bootstrap.Dropdown.getInstance(dropdown.previousElementSibling);
                        if (bsDropdown) bsDropdown.hide();
                    });

                    // Close modals
                    const modals = document.querySelectorAll('.modal.show');
                    modals.forEach(modal => {
                        const bsModal = bootstrap.Modal.getInstance(modal);
                        if (bsModal) bsModal.hide();
                    });
                }

                // Tab navigation improvements
                if (e.key === 'Tab') {
                    const activeElement = document.activeElement;

                    // Skip to main content (Ctrl/Cmd + Home)
                    if ((e.ctrlKey || e.metaKey) && e.key === 'Home') {
                        e.preventDefault();
                        const mainContent = document.querySelector('.content-area');
                        if (mainContent) {
                            mainContent.focus();
                            mainContent.scrollIntoView({ behavior: 'smooth' });
                        }
                    }
                }
            });

            // Add skip links for screen readers
            this.addSkipLinks();
        },

        addSkipLinks: function() {
            const skipLink = document.createElement('a');
            skipLink.href = '#main-content';
            skipLink.className = 'skip-link sr-only sr-only-focusable';
            skipLink.textContent = 'Skip to main content';
            skipLink.style.cssText = `
                position: absolute;
                top: -40px;
                left: 6px;
                background: #000;
                color: white;
                padding: 8px;
                z-index: 9999;
                text-decoration: none;
                border-radius: 4px;
                font-weight: 600;
            `;

            skipLink.addEventListener('focus', function() {
                this.style.top = '6px';
            });

            skipLink.addEventListener('blur', function() {
                this.style.top = '-40px';
            });

            document.body.insertBefore(skipLink, document.body.firstChild);

            // Add id to main content
            const mainContent = document.querySelector('.content-area');
            if (mainContent) {
                mainContent.id = 'main-content';
                mainContent.setAttribute('tabindex', '-1');
            }
        },

        initScreenReaderEnhancements: function() {
            // Add ARIA labels where missing
            const notificationBtn = document.querySelector('.topbar-notification');
            if (notificationBtn && !notificationBtn.getAttribute('aria-label')) {
                notificationBtn.setAttribute('aria-label', 'Notifications menu');
                notificationBtn.setAttribute('aria-haspopup', 'true');
            }

            const sidebarToggle = document.getElementById('sidebarToggle');
            if (sidebarToggle && !sidebarToggle.getAttribute('aria-label')) {
                sidebarToggle.setAttribute('aria-label', 'Toggle navigation menu');
                sidebarToggle.setAttribute('aria-expanded', 'false');
            }

            // Enhance form labels
            const formControls = document.querySelectorAll('.form-control');
            formControls.forEach(control => {
                if (!control.getAttribute('aria-describedby') && control.nextElementSibling?.classList.contains('invalid-feedback')) {
                    const errorId = control.id + '-error';
                    control.nextElementSibling.id = errorId;
                    control.setAttribute('aria-describedby', errorId);
                }
            });

            // Add live regions for dynamic content
            this.addLiveRegions();
        },

        addLiveRegions: function() {
            // Live region for notifications
            const notificationRegion = document.createElement('div');
            notificationRegion.id = 'notification-live-region';
            notificationRegion.setAttribute('aria-live', 'polite');
            notificationRegion.setAttribute('aria-atomic', 'true');
            notificationRegion.className = 'sr-only';
            document.body.appendChild(notificationRegion);

            // Live region for chat messages
            const chatRegion = document.createElement('div');
            chatRegion.id = 'chat-live-region';
            chatRegion.setAttribute('aria-live', 'assertive');
            chatRegion.setAttribute('aria-atomic', 'true');
            chatRegion.className = 'sr-only';
            document.body.appendChild(chatRegion);
        },

        initFocusManagement: function() {
            // Focus management for modals
            document.addEventListener('shown.bs.modal', function(e) {
                const modal = e.target;
                const focusableElements = modal.querySelectorAll(
                    'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
                );
                const firstElement = focusableElements[0];
                const lastElement = focusableElements[focusableElements.length - 1];

                if (firstElement) {
                    firstElement.focus();
                }

                // Trap focus within modal
                modal.addEventListener('keydown', function(e) {
                    if (e.key === 'Tab') {
                        if (e.shiftKey) {
                            if (document.activeElement === firstElement) {
                                lastElement.focus();
                                e.preventDefault();
                            }
                        } else {
                            if (document.activeElement === lastElement) {
                                firstElement.focus();
                                e.preventDefault();
                            }
                        }
                    }
                });
            });

            // Restore focus when modal closes
            document.addEventListener('hidden.bs.modal', function(e) {
                const trigger = document.querySelector('[data-bs-target="#' + e.target.id + '"]') ||
                               document.querySelector('[href="#' + e.target.id + '"]');
                if (trigger) {
                    trigger.focus();
                }
            });

            // Focus management for dropdowns
            document.addEventListener('shown.bs.dropdown', function(e) {
                const toggle = e.target;
                const menu = toggle.nextElementSibling;
                if (menu) {
                    const firstItem = menu.querySelector('[role="menuitem"], .dropdown-item');
                    if (firstItem) {
                        firstItem.focus();
                    }
                }
            });
        },

        initReducedMotion: function() {
            // Respect prefers-reduced-motion
            const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

            if (prefersReducedMotion) {
                // Disable animations and transitions
                const style = document.createElement('style');
                style.textContent = `
                    *, *::before, *::after {
                        animation-duration: 0.01ms !important;
                        animation-iteration-count: 1 !important;
                        transition-duration: 0.01ms !important;
                    }
                `;
                document.head.appendChild(style);
            }
        },

        // Announce content changes to screen readers
        announce: function(message, priority = 'polite') {
            const region = document.getElementById(
                priority === 'assertive' ? 'chat-live-region' : 'notification-live-region'
            );
            if (region) {
                region.textContent = message;
                // Clear after announcement
                setTimeout(() => {
                    region.textContent = '';
                }, 1000);
            }
        }
    },

    // Initialize accessibility features
    initAccessibility: function() {
        this.accessibility.init();
    }
};

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    OlivianSolar.init();
});

// Export for global use
window.OlivianSolar = OlivianSolar;
