/**
 * Comprehensive Cookie Management System
 * Handles cookie consent, preferences, and analytics integration
 */

class CookieManager {
    constructor() {
        this.consentData = {
            essential: 'pending',
            analytics: 'pending',
            marketing: 'pending',
            preferences: 'pending',
            social: 'pending'
        };

        this.categories = [];
        this.isInitialized = false;
        this.banner = null;
        this.modal = null;

        // Add consent expiry settings (30 days)
        this.consentExpiryDays = 30;
        this.hasValidConsent = false;

        // Initialize when DOM is ready
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.init());
        } else {
            this.init();
        }
    }

    async init() {
        try {
            console.log('Initializing cookie manager...');

            // Wait a bit to ensure DOM is fully loaded
            await new Promise(resolve => setTimeout(resolve, 200));

            // Check if banner exists
            this.banner = document.getElementById('cookie-banner');
            this.modal = document.getElementById('cookiePreferencesModal');

            console.log('DOM elements found:', {
                banner: !!this.banner,
                modal: !!this.modal,
                rejectBtn: !!document.getElementById('cookie-reject-all'),
                acceptBtn: !!document.getElementById('cookie-accept-all'),
                settingsBtn: !!document.getElementById('cookie-settings-btn')
            });

            if (!this.banner) {
                console.warn('Cookie banner not found in DOM');
                return;
            }

            // Set up Google CMP integration first
            this.setupGoogleCmpIntegration();

            // Load current consent status
            await this.loadConsentStatus();

            // Load cookie categories
            await this.loadCookieCategories();

            // Set up event listeners
            this.setupEventListeners();

            // Show banner if consent is needed
            this.checkAndShowBanner();

            // Apply current consent settings
            this.applyConsentSettings();

            this.isInitialized = true;

            console.log('Cookie manager initialized successfully');

            // Trigger initialization event
            this.triggerEvent('cookieManagerInitialized', { manager: this });

        } catch (error) {
            console.error('Error initializing cookie manager:', error);
        }
    }

    async loadConsentStatus() {
        // First, try to load from localStorage (primary for anonymous users)
        const localConsent = this.loadConsentFromStorage();

        // If local consent exists and is not expired, use it
        if (localConsent && !this.isConsentExpired()) {
            console.log('Using consent from localStorage');
            this.hasValidConsent = true;
            this.hasConsent = true;
            return;
        }

        // If local consent is expired or doesn't exist, check server
        try {
            const response = await fetch('/api/cookie-consent/status/', {
                method: 'GET',
                credentials: 'same-origin'
            });

            if (response.ok) {
                const data = await response.json();
                this.consentData = {
                    essential: data.essential || 'granted', // Always granted
                    analytics: data.analytics || 'pending',
                    marketing: data.marketing || 'pending',
                    preferences: data.preferences || 'pending',
                    social: data.social || 'pending'
                };

                // If server has consent, update localStorage
                if (data.has_consent) {
                    this.hasConsent = true;
                    this.hasValidConsent = true;
                    localStorage.setItem('cookieConsent', JSON.stringify(this.consentData));
                    localStorage.setItem('cookieConsentTimestamp', new Date().toISOString());
                    console.log('Updated localStorage from server');
                } else {
                    // No server consent and no valid local consent = show banner
                    this.hasConsent = false;
                    this.hasValidConsent = false;
                    console.log('No valid consent found - banner will show');
                }

            } else {
                console.warn('Failed to load consent status from server');
                // If API fails but we have local consent (even if expired), use it for now
                if (localConsent) {
                    this.hasConsent = true;
                    this.hasValidConsent = false; // Mark as needing renewal
                    console.log('API failed - using expired local consent temporarily');
                }
            }
        } catch (error) {
            console.error('Error loading consent status:', error);
            // On API failure, if we have any local consent, use it
            if (localConsent) {
                this.hasConsent = true;
                this.hasValidConsent = false;
                console.log('API error - using local consent as fallback');
            }
        }
    }

    loadConsentFromStorage() {
        const stored = localStorage.getItem('cookieConsent');
        if (stored) {
            try {
                this.consentData = JSON.parse(stored);
                return true;
            } catch (error) {
                console.error('Error parsing stored consent data:', error);
                return false;
            }
        }
        return false;
    }

    isConsentExpired() {
        const timestamp = localStorage.getItem('cookieConsentTimestamp');
        if (!timestamp) return true;

        try {
            const consentDate = new Date(timestamp);
            const now = new Date();
            const daysDiff = (now - consentDate) / (1000 * 60 * 60 * 24);
            return daysDiff > this.consentExpiryDays;
        } catch (error) {
            console.error('Error checking consent expiry:', error);
            return true;
        }
    }

    async loadCookieCategories() {
        try {
            const response = await fetch('/api/cookie-categories/', {
                method: 'GET',
                credentials: 'same-origin'
            });
            
            if (response.ok) {
                const data = await response.json();
                this.categories = data.categories || [];
            }
        } catch (error) {
            console.error('Error loading cookie categories:', error);
        }
    }

    setupEventListeners() {
        console.log('Setting up cookie manager event listeners...');
        
        // Banner buttons
        const acceptAllBtn = document.getElementById('cookie-accept-all');
        const rejectAllBtn = document.getElementById('cookie-reject-all');
        const settingsBtn = document.getElementById('cookie-settings-btn');
        
        console.log('Found elements:', {
            acceptAllBtn: !!acceptAllBtn,
            rejectAllBtn: !!rejectAllBtn,
            settingsBtn: !!settingsBtn,
            banner: !!this.banner,
            modal: !!this.modal
        });
        
        if (acceptAllBtn) {
            acceptAllBtn.addEventListener('click', () => this.acceptAll());
        }
        
        if (rejectAllBtn) {
            console.log('Adding click listener to reject all button');
            rejectAllBtn.addEventListener('click', (e) => {
                console.log('Reject all button clicked!');
                e.preventDefault();
                this.rejectAll();
            });
        } else {
            console.warn('Reject all button not found!');
        }
        
        if (settingsBtn) {
            console.log('Adding click listener to settings button');
            settingsBtn.addEventListener('click', (e) => {
                console.log('Settings button clicked!');
                e.preventDefault();
                this.showPreferences();
            });
        } else {
            console.warn('Settings button not found!');
        }

        // Modal buttons
        const savePreferencesBtn = document.getElementById('save-cookie-preferences');
        if (savePreferencesBtn) {
            savePreferencesBtn.addEventListener('click', () => this.savePreferences());
        }

        // Listen for modal show event to populate categories
        if (this.modal) {
            this.modal.addEventListener('shown.bs.modal', () => {
                this.populateCookieCategories();
            });
        }
    }

    checkAndShowBanner() {
        // For anonymous users, be more thoughtful about when to show banner
        const isLoggedIn = window.user && window.user.is_authenticated;

        // Logged-in users: standard behavior
        if (isLoggedIn) {
            if (!this.hasConsent && this.banner) {
                console.log('Showing banner for logged-in user without consent');
                this.showBanner();
            }
            return;
        }

        // Anonymous users: more forgiving approach
        // Don't show banner if:
        // 1. We have any recent consent in localStorage
        // 2. We've recently checked server (within last hour) - reduce API calls
        if (!this.hasValidConsent) {
            const lastCheck = localStorage.getItem('lastConsentCheck');
            const now = new Date().getTime();

            if (lastCheck) {
                const hoursSinceCheck = (now - parseInt(lastCheck)) / (1000 * 60 * 60);
                if (hoursSinceCheck < 1) { // Wait at least 1 hour between banner shows
                    console.log('Skipping banner - recent consent check');
                    return;
                }
            }

            // Mark this check time
            localStorage.setItem('lastConsentCheck', now.toString());

            // Only show banner if we genuinely have no consent
            if (!this.hasConsent && this.banner) {
                console.log('Showing banner for anonymous user');
                this.showBanner();
            } else if (this.hasConsent && this.hasValidConsent === false) {
                // Have consent but it's expired - don't spam with banner, silently renew if possible
                console.log('Consent exists but expired - not showing banner yet');
            }
        }
    }

    showBanner() {
        if (this.banner) {
            this.banner.style.display = 'block';
            // Add slight delay for animation
            setTimeout(() => {
                this.banner.classList.add('show');
            }, 100);
        }
    }

    hideBanner() {
        console.log('hideBanner() called, banner element:', this.banner);
        if (this.banner) {
            console.log('Hiding banner...');
            this.banner.classList.add('hide');
            setTimeout(() => {
                this.banner.style.display = 'none';
                this.banner.classList.remove('hide');
                console.log('Banner hidden');
            }, 500);
        } else {
            console.warn('Cannot hide banner - banner element not found');
        }
    }

    async acceptAll() {
        this.consentData = {
            essential: 'granted',
            analytics: 'granted',
            marketing: 'granted',
            preferences: 'granted',
            social: 'granted'
        };
        
        await this.saveConsentSettings();
        this.hideBanner();
        this.applyConsentSettings();
        this.triggerEvent('cookieConsentChanged', { consent: this.consentData, type: 'acceptAll' });
    }

    async rejectAll() {
        console.log('rejectAll() method called');
        
        this.consentData = {
            essential: 'granted',
            analytics: 'denied',
            marketing: 'denied', 
            preferences: 'denied',
            social: 'denied'
        };
        
        console.log('Saving consent settings...');
        await this.saveConsentSettings();
        
        console.log('Hiding banner...');
        this.hideBanner();
        
        console.log('Applying consent settings...');
        this.applyConsentSettings();
        
        console.log('Triggering event...');
        this.triggerEvent('cookieConsentChanged', { consent: this.consentData, type: 'rejectAll' });
        
        console.log('rejectAll() method completed');
    }

    showPreferences() {
        if (this.modal && window.bootstrap) {
            console.log('Opening cookie preferences modal');
            
            // Hide the banner when showing preferences
            this.hideBanner();
            
            const modal = new bootstrap.Modal(this.modal);
            modal.show();
            
            // Add event listener to show banner again if modal is closed without saving
            this.modal.addEventListener('hidden.bs.modal', () => {
                console.log('Modal closed, hasConsent:', this.hasConsent);
                // Only show banner again if user hasn't given consent
                if (!this.hasConsent) {
                    console.log('Showing banner again because no consent given');
                    this.showBanner();
                } else {
                    console.log('Banner remains hidden - user has given consent');
                }
            }, { once: true }); // Use once: true so the listener is removed after first use
        }
    }

    populateCookieCategories() {
        const container = document.getElementById('cookie-categories-container');
        if (!container || !this.categories.length) return;

        let html = '';
        
        this.categories.forEach(category => {
            const isEssential = category.is_essential;
            const currentConsent = this.consentData[category.name] === 'granted';
            
            html += `
                <div class="cookie-category">
                    <div class="cookie-category-header ${isEssential ? 'essential' : ''}" 
                         onclick="this.parentElement.querySelector('.cookie-category-details').classList.toggle('show')">
                        <div class="cookie-category-info">
                            <h6>${category.display_name}</h6>
                            <p>${category.description}</p>
                        </div>
                        <div class="cookie-toggle">
                            <label class="cookie-switch">
                                <input type="checkbox" 
                                       data-category="${category.name}"
                                       ${currentConsent ? 'checked' : ''}
                                       ${isEssential ? 'disabled' : ''}
                                       onchange="window.cookieManager.updateCategoryConsent('${category.name}', this.checked)">
                                <span class="cookie-slider"></span>
                            </label>
                            ${isEssential ? '<small class="text-muted ms-2">Always On</small>' : ''}
                        </div>
                    </div>
                    <div class="cookie-category-details">
                        <p><strong>Purpose:</strong> ${category.description}</p>
                        ${category.cookies.length ? this.renderCookieTable(category.cookies) : '<p><em>No specific cookies listed for this category.</em></p>'}
                    </div>
                </div>
            `;
        });
        
        container.innerHTML = html;
    }

    renderCookieTable(cookies) {
        let html = `
            <table class="cookie-details-table">
                <thead>
                    <tr>
                        <th>Cookie Name</th>
                        <th>Purpose</th>
                        <th>Duration</th>
                        <th>Provider</th>
                    </tr>
                </thead>
                <tbody>
        `;
        
        cookies.forEach(cookie => {
            html += `
                <tr>
                    <td><code>${cookie.name}</code></td>
                    <td>${cookie.purpose}</td>
                    <td>${cookie.duration}</td>
                    <td>${cookie.provider || (cookie.third_party ? 'Third Party' : 'First Party')}</td>
                </tr>
            `;
        });
        
        html += `
                </tbody>
            </table>
        `;
        
        return html;
    }

    updateCategoryConsent(category, granted) {
        this.consentData[category] = granted ? 'granted' : 'denied';
    }

    async savePreferences() {
        await this.saveConsentSettings();
        
        // Close modal
        if (this.modal && window.bootstrap) {
            const modal = bootstrap.Modal.getInstance(this.modal);
            if (modal) modal.hide();
        }
        
        // Ensure banner is hidden since user has now given consent
        this.hideBanner();
        this.hasConsent = true; // Explicitly set this to ensure banner doesn't show again
        
        this.applyConsentSettings();
        this.triggerEvent('cookieConsentChanged', { consent: this.consentData, type: 'savePreferences' });
        
        // Show success message
        this.showNotification('Cookie preferences saved successfully!', 'success');
    }

    async saveConsentSettings() {
        try {
            const response = await fetch('/api/cookie-consent/update/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                credentials: 'same-origin',
                body: JSON.stringify(this.consentData)
            });
            
            if (response.ok) {
                this.hasConsent = true;
                localStorage.setItem('cookieConsent', JSON.stringify(this.consentData));
                localStorage.setItem('cookieConsentTimestamp', new Date().toISOString());
            } else {
                throw new Error('Failed to save consent settings');
            }
            
        } catch (error) {
            console.error('Error saving consent settings:', error);
            this.showNotification('Error saving cookie preferences', 'error');
        }
    }

    applyConsentSettings() {
        // Analytics consent
        if (this.consentData.analytics === 'granted') {
            this.enableAnalytics();
        } else {
            this.disableAnalytics();
        }

        // Marketing consent
        if (this.consentData.marketing === 'granted') {
            this.enableMarketing();
        } else {
            this.disableMarketing();
        }

        // Social media consent
        if (this.consentData.social === 'granted') {
            this.enableSocial();
        } else {
            this.disableSocial();
        }

        // Preferences consent
        if (this.consentData.preferences === 'granted') {
            this.enablePreferences();
        } else {
            this.disablePreferences();
        }

        // Update Google CMP consent
        this.updateGoogleCmpConsent();
    }

    enableAnalytics() {
        // Google Analytics 4
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'granted'
            });
        }
        
        // Google Analytics (Universal Analytics)
        if (typeof ga !== 'undefined') {
            ga('set', 'anonymizeIp', false);
        }
        
        // Custom analytics code can be added here
        this.triggerEvent('analyticsEnabled');
    }

    disableAnalytics() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'analytics_storage': 'denied'
            });
        }
        
        this.triggerEvent('analyticsDisabled');
    }

    enableMarketing() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'ad_storage': 'granted'
            });
        }
        
        this.triggerEvent('marketingEnabled');
    }

    disableMarketing() {
        if (typeof gtag !== 'undefined') {
            gtag('consent', 'update', {
                'ad_storage': 'denied'
            });
        }
        
        this.triggerEvent('marketingDisabled');
    }

    enableSocial() {
        // Re-enable social media widgets/scripts
        this.triggerEvent('socialEnabled');
    }

    disableSocial() {
        // Disable social media tracking
        this.triggerEvent('socialDisabled');
    }

    enablePreferences() {
        this.triggerEvent('preferencesEnabled');
    }

    disablePreferences() {
        this.triggerEvent('preferencesDisabled');
    }

    getCSRFToken() {
        const tokenElement = document.querySelector('[name=csrfmiddlewaretoken]');
        return tokenElement ? tokenElement.value : '';
    }

    triggerEvent(eventName, detail = {}) {
        const event = new CustomEvent(eventName, { detail });
        document.dispatchEvent(event);
    }

    showNotification(message, type = 'info') {
        // Create notification element if it doesn't exist
        let notification = document.createElement('div');
        notification.className = `alert alert-${type === 'error' ? 'danger' : type} alert-dismissible fade show cookie-notification`;
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Position notification
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10001;
            min-width: 300px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
        `;
        
        document.body.appendChild(notification);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }

    // Public API methods
    hasConsentFor(category) {
        return this.consentData[category] === 'granted';
    }

    getConsentData() {
        return { ...this.consentData };
    }

    async updateConsent(newConsent) {
        this.consentData = { ...this.consentData, ...newConsent };
        await this.saveConsentSettings();
        this.applyConsentSettings();
    }

    async revokeConsent() {
        this.consentData = {
            essential: 'granted',
            analytics: 'denied',
            marketing: 'denied',
            preferences: 'denied',
            social: 'denied'
        };

        await this.saveConsentSettings();
        this.applyConsentSettings();
        this.showBanner();
    }

    // Google CMP Integration
    setupGoogleCmpIntegration() {
        console.log('Setting up Google CMP integration...');

        // Listen for Google CMP consent events
        document.addEventListener('googleCmpConsent', (event) => {
            const consentData = event.detail;
            console.log('Received Google CMP consent:', consentData);

            // Update our consent data based on Google CMP
            if (consentData.consentState) {
                const googleConsent = consentData.consentState;

                // Map Google consent to our categories
                if (googleConsent.adStorage === 'granted') {
                    this.consentData.marketing = 'granted';
                } else if (googleConsent.adStorage === 'denied') {
                    this.consentData.marketing = 'denied';
                }

                if (googleConsent.analyticsStorage === 'granted') {
                    this.consentData.analytics = 'granted';
                } else if (googleConsent.analyticsStorage === 'denied') {
                    this.consentData.analytics = 'denied';
                }

                // Update local storage
                localStorage.setItem('cookieConsent', JSON.stringify(this.consentData));
                localStorage.setItem('cookieConsentTimestamp', new Date().toISOString());

                // Apply the consent settings
                this.applyConsentSettings();

                // Hide banner if consent was given
                if (googleConsent.adStorage === 'granted' || googleConsent.analyticsStorage === 'granted') {
                    this.hasConsent = true;
                    this.hideBanner();
                    console.log('Banner hidden due to Google CMP consent');
                }

                console.log('Updated consent from Google CMP:', this.consentData);
            }
        });

        // Check if Google CMP is already loaded and has consent data
        if (window.googlefc && window.googlefc.getConsentStatus) {
            try {
                const status = window.googlefc.getConsentStatus();
                if (status && status.consentState) {
                    console.log('Google CMP already has consent data:', status);
                    // Trigger our event handler
                    document.dispatchEvent(new CustomEvent('googleCmpConsent', {
                        detail: status
                    }));
                }
            } catch (error) {
                console.log('Error checking Google CMP status:', error);
            }
        }

        console.log('Google CMP integration setup complete');
    }

    // Method to update Google CMP when our consent changes
    updateGoogleCmpConsent() {
        if (typeof gtag !== 'undefined') {
            // Update Google Analytics consent based on our consent data
            gtag('consent', 'update', {
                'ad_storage': this.consentData.marketing === 'granted' ? 'granted' : 'denied',
                'ad_user_data': this.consentData.marketing === 'granted' ? 'granted' : 'denied',
                'ad_personalization': this.consentData.marketing === 'granted' ? 'granted' : 'denied',
                'analytics_storage': this.consentData.analytics === 'granted' ? 'granted' : 'denied'
            });
            console.log('Updated Google CMP consent from our system');
        }
    }
}

// Initialize global cookie manager
window.cookieManager = new CookieManager();

// Utility functions for other scripts to use
window.cookieConsent = {
    hasConsent: (category) => window.cookieManager.hasConsentFor(category),
    getData: () => window.cookieManager.getConsentData(),
    update: (consent) => window.cookieManager.updateConsent(consent),
    revoke: () => window.cookieManager.revokeConsent(),
    showPreferences: () => window.cookieManager.showPreferences()
};

// Legacy support for Google Analytics
window.dataLayer = window.dataLayer || [];
function gtag(){dataLayer.push(arguments);}

// Initialize Google Analytics consent mode if gtag is available
if (typeof gtag !== 'undefined') {
    gtag('consent', 'default', {
        'analytics_storage': 'denied',
        'ad_storage': 'denied',
        'wait_for_update': 500,
    });
}
