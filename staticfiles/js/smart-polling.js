/**
 * Smart Polling Manager - Adaptive polling with exponential backoff
 * Reduces server load by intelligently adjusting polling intervals based on activity
 */

class SmartPollingManager {
    constructor() {
        this.polls = new Map();
        this.networkStatus = navigator.onLine;
        this.pageVisible = !document.hidden;
        this.initialized = false;

        this.init();
    }

    init() {
        if (this.initialized) return;
        this.initialized = true;

        // Listen for network changes
        window.addEventListener('online', () => {
            this.networkStatus = true;
            this.onNetworkChange();
        });

        window.addEventListener('offline', () => {
            this.networkStatus = false;
            this.onNetworkChange();
        });

        // Listen for page visibility changes
        document.addEventListener('visibilitychange', () => {
            this.pageVisible = !document.hidden;
            this.onVisibilityChange();
        });

        console.log('Smart Polling Manager initialized');
    }

    /**
     * Register a new polling task
     * @param {string} id - Unique identifier for the poll
     * @param {Object} config - Polling configuration
     */
    register(id, config) {
        const defaultConfig = {
            url: '',
            method: 'GET',
            headers: {},
            interval: 3000,        // Base interval in milliseconds
            maxInterval: 30000,    // Maximum interval (30 seconds)
            backoffFactor: 2,      // Exponential backoff multiplier
            successCallback: null,
            errorCallback: null,
            dataCallback: null,    // Callback for processing response data
            enabled: true,
            pauseOnBlur: true,     // Pause when page is not visible
            pauseOffline: true,    // Pause when offline
            retryOnError: true,
            maxRetries: 3,
            timeout: 10000,        // Request timeout
        };

        const pollConfig = { ...defaultConfig, ...config };
        const pollState = {
            id,
            config: pollConfig,
            intervalId: null,
            currentInterval: pollConfig.interval,
            consecutiveErrors: 0,
            consecutiveEmpty: 0,
            lastSuccess: null,
            lastActivity: Date.now(),
            retryCount: 0,
            activeRequest: null,
            abortController: null,
        };

        this.polls.set(id, pollState);

        if (pollConfig.enabled) {
            this.start(id);
        }

        console.log(`Registered polling task: ${id}`, pollConfig);
    }

    /**
     * Start polling for a registered task
     */
    start(id) {
        const poll = this.polls.get(id);
        if (!poll) return;

        this.stop(id); // Stop any existing polling

        poll.config.enabled = true;
        this.scheduleNextPoll(id);
        console.log(`Started polling: ${id}`);
    }

    /**
     * Stop polling for a task
     */
    stop(id) {
        const poll = this.polls.get(id);
        if (!poll) return;

        poll.config.enabled = false;

        if (poll.intervalId) {
            clearTimeout(poll.intervalId);
            poll.intervalId = null;
        }

        if (poll.abortController) {
            poll.abortController.abort();
            poll.abortController = null;
        }

        console.log(`Stopped polling: ${id}`);
    }

    /**
     * Update configuration for a polling task
     */
    updateConfig(id, config) {
        const poll = this.polls.get(id);
        if (!poll) return;

        poll.config = { ...poll.config, ...config };

        // Restart if enabled and currently running
        if (poll.config.enabled && poll.intervalId) {
            this.start(id);
        }
    }

    /**
     * Force immediate execution of a polling task
     */
    pollNow(id) {
        const poll = this.polls.get(id);
        if (!poll || !poll.config.enabled) return;

        // Cancel any pending poll
        if (poll.intervalId) {
            clearTimeout(poll.intervalId);
            poll.intervalId = null;
        }

        this.executePoll(id);
    }

    /**
     * Reset polling interval to base value (call when new data is detected)
     */
    resetInterval(id) {
        const poll = this.polls.get(id);
        if (!poll) return;

        poll.currentInterval = poll.config.interval;
        poll.consecutiveEmpty = 0;
        poll.lastActivity = Date.now();

        console.log(`Reset interval for ${id} to ${poll.currentInterval}ms`);
    }

    /**
     * Remove a polling task
     */
    remove(id) {
        this.stop(id);
        this.polls.delete(id);
        console.log(`Removed polling task: ${id}`);
    }

    /**
     * Schedule the next poll execution
     */
    scheduleNextPoll(id) {
        const poll = this.polls.get(id);
        if (!poll || !poll.config.enabled) return;

        // Check if we should pause
        if (this.shouldPause(poll)) {
            console.log(`Pausing poll ${id} (visibility: ${this.pageVisible}, network: ${this.networkStatus})`);
            return;
        }

        const adjustedInterval = this.calculateInterval(poll);
        poll.intervalId = setTimeout(() => {
            this.executePoll(id);
        }, adjustedInterval);

        console.log(`Next poll for ${id} scheduled in ${adjustedInterval}ms`);
    }

    /**
     * Execute the actual polling request
     */
    async executePoll(id) {
        const poll = this.polls.get(id);
        if (!poll || !poll.config.enabled || this.shouldPause(poll)) return;

        // Prevent overlapping requests
        if (poll.activeRequest) {
            console.log(`Skipping overlapping poll for ${id}`);
            this.scheduleNextPoll(id);
            return;
        }

        try {
            // Create abort controller for this request
            poll.abortController = new AbortController();
            const timeoutId = setTimeout(() => {
                poll.abortController.abort();
            }, poll.config.timeout);

            const requestConfig = {
                method: poll.config.method,
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    ...poll.config.headers
                },
                signal: poll.abortController.signal
            };

            // Add body for non-GET requests
            if (poll.config.method !== 'GET' && poll.config.body) {
                requestConfig.body = poll.config.body;
            }

            poll.activeRequest = true;
            console.log(`Executing poll: ${id} -> ${poll.config.url}`);

            const response = await fetch(poll.config.url, requestConfig);
            clearTimeout(timeoutId);

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }

            const data = await response.json();

            // Process the response
            this.handlePollSuccess(id, data);

        } catch (error) {
            this.handlePollError(id, error);
        } finally {
            poll.activeRequest = false;
            poll.abortController = null;

            // Schedule next poll regardless of success/failure
            this.scheduleNextPoll(id);
        }
    }

    /**
     * Handle successful polling response
     */
    handlePollSuccess(id, data) {
        const poll = this.polls.get(id);
        if (!poll) return;

        poll.consecutiveErrors = 0;
        poll.retryCount = 0;
        poll.lastSuccess = Date.now();

        // Check if response has new data
        let hasNewData = true;
        if (poll.config.dataCallback) {
            hasNewData = poll.config.dataCallback(data);
        } else if (data && typeof data === 'object') {
            // Default check: look for messages array or similar data indicators
            hasNewData = (data.messages && data.messages.length > 0) ||
                        (data.unread_count && data.unread_count > 0) ||
                        (data.typing_users && data.typing_users.length > 0) ||
                        (data.online_users && data.online_users.length > 0) ||
                        (data.success === true);
        }

        if (hasNewData) {
            poll.consecutiveEmpty = 0;
            poll.lastActivity = Date.now();
            this.resetInterval(id);
        } else {
            poll.consecutiveEmpty++;
        }

        // Call success callback
        if (poll.config.successCallback) {
            poll.config.successCallback(data);
        }

        console.log(`Poll success: ${id} (hasData: ${hasNewData}, emptyCount: ${poll.consecutiveEmpty})`);
    }

    /**
     * Handle polling error
     */
    handlePollError(id, error) {
        const poll = this.polls.get(id);
        if (!poll) return;

        poll.consecutiveErrors++;

        // Don't increment empty count on network errors
        if (error.name === 'TypeError' || error.message.includes('fetch')) {
            // Network error - don't count as empty response
        } else if (poll.consecutiveErrors === 1) {
            // First error might be temporary, don't count as empty yet
        }

        console.warn(`Poll error for ${id}:`, error.message);

        // Handle retries
        if (poll.config.retryOnError && poll.consecutiveErrors <= poll.config.maxRetries) {
            poll.retryCount++;
            console.log(`Retrying poll ${id} (attempt ${poll.retryCount}/${poll.config.maxRetries})`);

            // Schedule retry with shorter interval
            setTimeout(() => {
                if (poll.config.enabled) {
                    this.executePoll(id);
                }
            }, Math.min(1000 * Math.pow(2, poll.retryCount), 5000)); // Exponential backoff, max 5 seconds
            return;
        }

        // Call error callback
        if (poll.config.errorCallback) {
            poll.config.errorCallback(error);
        }
    }

    /**
     * Calculate the next polling interval based on activity
     */
    calculateInterval(poll) {
        const config = poll.config;
        let interval = poll.currentInterval;

        // Base interval adjustment based on consecutive empty responses
        if (poll.consecutiveEmpty > 0) {
            // Exponential backoff for empty responses, but slower than error backoff
            const backoffMultiplier = Math.pow(1.5, Math.min(poll.consecutiveEmpty, 5));
            interval = Math.min(interval * backoffMultiplier, config.maxInterval);
        }

        // Network status adjustment
        if (!this.networkStatus && config.pauseOffline) {
            interval = Math.max(interval, 10000); // At least 10 seconds when offline
        }

        // Visibility adjustment
        if (!this.pageVisible && config.pauseOnBlur) {
            interval = Math.max(interval, 15000); // At least 15 seconds when not visible
        }

        // Activity-based adjustment
        const timeSinceActivity = Date.now() - poll.lastActivity;
        if (timeSinceActivity > 5 * 60 * 1000) { // 5 minutes of inactivity
            interval = Math.min(interval * 1.5, config.maxInterval);
        }

        // Ensure minimum interval
        interval = Math.max(interval, 1000); // Minimum 1 second

        // Update current interval for next calculation
        poll.currentInterval = interval;

        return interval;
    }

    /**
     * Check if polling should be paused
     */
    shouldPause(poll) {
        if (!poll.config.pauseOnBlur && !this.pageVisible) return false;
        if (!poll.config.pauseOffline && !this.networkStatus) return false;

        return (poll.config.pauseOnBlur && !this.pageVisible) ||
               (poll.config.pauseOffline && !this.networkStatus);
    }

    /**
     * Handle network status changes
     */
    onNetworkChange() {
        console.log(`Network status changed: ${this.networkStatus ? 'online' : 'offline'}`);

        // Restart all polls to apply new network-aware intervals
        for (const [id, poll] of this.polls) {
            if (poll.config.enabled) {
                this.start(id);
            }
        }
    }

    /**
     * Handle page visibility changes
     */
    onVisibilityChange() {
        console.log(`Page visibility changed: ${this.pageVisible ? 'visible' : 'hidden'}`);

        if (this.pageVisible) {
            // Page became visible, reset intervals for active polling
            for (const [id, poll] of this.polls) {
                if (poll.config.enabled) {
                    this.resetInterval(id);
                    this.start(id);
                }
            }
        }
    }

    /**
     * Get status information for monitoring/debugging
     */
    getStatus() {
        const status = {};
        for (const [id, poll] of this.polls) {
            status[id] = {
                enabled: poll.config.enabled,
                currentInterval: poll.currentInterval,
                consecutiveEmpty: poll.consecutiveEmpty,
                consecutiveErrors: poll.consecutiveErrors,
                lastActivity: poll.lastActivity,
                lastSuccess: poll.lastSuccess,
                activeRequest: poll.activeRequest !== null,
                paused: this.shouldPause(poll)
            };
        }
        return status;
    }

    /**
     * Cleanup all polling tasks
     */
    destroy() {
        for (const [id, poll] of this.polls) {
            this.stop(id);
        }
        this.polls.clear();
        console.log('Smart Polling Manager destroyed');
    }
}

// Global instance
window.SmartPollingManager = new SmartPollingManager();

// Make it available globally for debugging
window.smartPolling = window.SmartPollingManager;
