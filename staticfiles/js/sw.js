// Olivian Group - Service Worker for PWA
const CACHE_NAME = 'olivian-v1.0.2';
const STATIC_CACHE_NAME = 'olivian-static-v1.0.2';
const DYNAMIC_CACHE_NAME = 'olivian-dynamic-v1.0.2';

// IndexedDB database name and version
const DB_NAME = 'OlivianOfflineDB';
const DB_VERSION = 1;

// IndexedDB helper function
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;

            // Create object stores if they don't exist
            if (!db.objectStoreNames.contains('pendingChatMessages')) {
                db.createObjectStore('pendingChatMessages', { keyPath: 'id', autoIncrement: true });
            }
            if (!db.objectStoreNames.contains('pendingForms')) {
                db.createObjectStore('pendingForms', { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

// Resources to cache immediately
const STATIC_ASSETS = [
    '/',
    '/static/css/main.css',
    '/static/css/dashboard.css',
    '/static/css/forms.css',
    '/static/css/chat_room.css',
    '/static/js/main.js',
    '/static/js/smart-polling.js',
    '/static/js/api.js',
    '/static/js/dashboard.js',
    '/static/manifest.json',
    '/static/images/logo.png',
    '/offline.html'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('[ServiceWorker] Install');
    event.waitUntil(
        caches.open(STATIC_CACHE_NAME)
            .then(cache => {
                console.log('[ServiceWorker] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[ServiceWorker] Skip waiting');
                return self.skipWaiting();
            })
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[ServiceWorker] Activate');
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== STATIC_CACHE_NAME && cacheName !== DYNAMIC_CACHE_NAME) {
                        console.log('[ServiceWorker] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[ServiceWorker] Claiming clients');
            return self.clients.claim();
        })
    );
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }

    // Handle API requests specially
    if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/chat/api/')) {
        event.respondWith(
            caches.open(DYNAMIC_CACHE_NAME)
                .then(cache => {
                    return fetch(request)
                        .then(response => {
                            // Cache successful responses
                            if (response.status === 200) {
                                cache.put(request, response.clone());
                            }
                            return response;
                        })
                        .catch(() => {
                            // Return cached version if available, otherwise offline page
                            return cache.match(request)
                                .then(cachedResponse => {
                                    if (cachedResponse) {
                                        return cachedResponse;
                                    }
                                    // Return offline page for API failures
                                    return caches.match('/offline.html');
                                });
                        });
                })
        );
        return;
    }

    // Handle static assets - network first, fallback to cache
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Cache successful responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(STATIC_CACHE_NAME)
                            .then(cache => cache.put(request, responseClone));
                    }
                    return response;
                })
                .catch(() => {
                    // Return cached version
                    return caches.match(request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // Return a basic offline response for missing assets
                            return new Response('Asset temporarily unavailable', {
                                status: 503,
                                statusText: 'Service Unavailable'
                            });
                        });
                })
        );
        return;
    }

    // Handle media files - network first, no caching, proper 404 handling
    if (url.pathname.startsWith('/media/')) {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Return the response as-is (including 404s)
                    return response;
                })
                .catch(() => {
                    // Network failure - return proper 404
                    return new Response('File not found', {
                        status: 404,
                        statusText: 'Not Found'
                    });
                })
        );
        return;
    }

    // Handle page requests - network first, fallback to cache
    if (request.destination === 'document' ||
        (request.method === 'GET' && !url.pathname.includes('.'))) {

        event.respondWith(
            fetch(request)
                .then(response => {
                    // Cache successful page responses for offline use
                    if (response.status === 200 && response.type === 'basic') {
                        const responseClone = response.clone();
                        caches.open(DYNAMIC_CACHE_NAME)
                            .then(cache => cache.put(request, responseClone));
                    }
                    return response;
                })
                .catch(() => {
                    // Return cached version if network fails
                    return caches.match(request)
                        .then(cachedResponse => {
                            if (cachedResponse) {
                                return cachedResponse;
                            }
                            // Return offline page for failed page requests
                            return caches.match('/offline.html');
                        });
                })
        );
        return;
    }

    // Default fallback for other requests
    event.respondWith(fetch(request));
});

// Background sync for offline actions
self.addEventListener('sync', event => {
    console.log('[ServiceWorker] Background sync:', event.tag);

    if (event.tag === 'background-sync-chat') {
        event.waitUntil(syncChatMessages());
    }

    if (event.tag === 'background-sync-forms') {
        event.waitUntil(syncFormSubmissions());
    }
});

// Push notifications
self.addEventListener('push', event => {
    console.log('[ServiceWorker] Push received');

    let data = {};
    if (event.data) {
        data = event.data.json();
    }

    const options = {
        body: data.body || 'You have a new notification',
        icon: '/static/images/logo.png',
        badge: '/static/images/logo.png',
        vibrate: [200, 100, 200],
        data: {
            url: data.url || '/',
            id: data.id
        },
        actions: [
            {
                action: 'view',
                title: 'View',
                icon: '/static/images/logo.png'
            },
            {
                action: 'dismiss',
                title: 'Dismiss'
            }
        ],
        requireInteraction: true,
        silent: false,
        tag: data.tag || 'general-notification',
        renotify: true
    };

    event.waitUntil(
        self.registration.showNotification(
            data.title || 'Olivian Group',
            options
        )
    );
});

// Push notification click handler
self.addEventListener('notificationclick', event => {
    console.log('[ServiceWorker] Notification click:', event.action);

    event.notification.close();

    if (event.action === 'dismiss') {
        return;
    }

    const urlToOpen = event.notification.data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then(windowClients => {
                // Check if there's already a window/tab open with the target URL
                const existingWindow = windowClients.find(client =>
                    client.url === urlToOpen || client.url.startsWith(urlToOpen)
                );

                if (existingWindow) {
                    // Focus existing window
                    return existingWindow.focus();
                } else {
                    // Open new window
                    return clients.openWindow(urlToOpen);
                }
            })
    );
});

// Background sync functions
async function syncChatMessages() {
    try {
        console.log('[ServiceWorker] Syncing chat messages');
        // Get pending messages from IndexedDB
        const pendingMessages = await getPendingChatMessages();

        for (const message of pendingMessages) {
            try {
                const response = await fetch('/chat/api/messages/send/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(message)
                });

                if (response.ok) {
                    await removePendingMessage(message.id);
                    console.log('[ServiceWorker] Synced message:', message.id);
                }
            } catch (error) {
                console.error('[ServiceWorker] Failed to sync message:', message.id, error);
            }
        }
    } catch (error) {
        console.error('[ServiceWorker] Background sync error:', error);
    }
}

async function syncFormSubmissions() {
    try {
        console.log('[ServiceWorker] Syncing form submissions');
        const pendingForms = await getPendingForms();

        for (const form of pendingForms) {
            try {
                const response = await fetch(form.url, {
                    method: form.method,
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCsrfToken()
                    },
                    body: JSON.stringify(form.data)
                });

                if (response.ok) {
                    await removePendingForm(form.id);
                    console.log('[ServiceWorker] Synced form:', form.id);
                }
            } catch (error) {
                console.error('[ServiceWorker] Failed to sync form:', form.id, error);
            }
        }
    } catch (error) {
        console.error('[ServiceWorker] Form sync error:', error);
    }
}

// Helper functions using IndexedDB for offline data storage
async function getPendingChatMessages() {
    try {
        const db = await openDB();
        const transaction = db.transaction(['pendingChatMessages'], 'readonly');
        const store = transaction.objectStore('pendingChatMessages');
        const request = store.getAll();

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error('[ServiceWorker] Error getting pending chat messages:', error);
        return [];
    }
}

async function getPendingForms() {
    try {
        const db = await openDB();
        const transaction = db.transaction(['pendingForms'], 'readonly');
        const store = transaction.objectStore('pendingForms');
        const request = store.getAll();

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error('[ServiceWorker] Error getting pending forms:', error);
        return [];
    }
}

async function removePendingMessage(id) {
    try {
        const db = await openDB();
        const transaction = db.transaction(['pendingChatMessages'], 'readwrite');
        const store = transaction.objectStore('pendingChatMessages');
        const request = store.delete(id);

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error('[ServiceWorker] Error removing pending message:', error);
        throw error;
    }
}

async function removePendingForm(id) {
    try {
        const db = await openDB();
        const transaction = db.transaction(['pendingForms'], 'readwrite');
        const store = transaction.objectStore('pendingForms');
        const request = store.delete(id);

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error('[ServiceWorker] Error removing pending form:', error);
        throw error;
    }
}

// Message handling from main thread - extended to handle data storage
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }

    // Handle adding pending data from main thread
    if (event.data && event.data.type === 'ADD_PENDING_MESSAGE') {
        addPendingMessage(event.data.message);
    }

    if (event.data && event.data.type === 'ADD_PENDING_FORM') {
        addPendingForm(event.data.form);
    }
});

// Helper functions to add pending data from main thread
async function addPendingMessage(message) {
    try {
        const db = await openDB();
        const transaction = db.transaction(['pendingChatMessages'], 'readwrite');
        const store = transaction.objectStore('pendingChatMessages');
        const request = store.add(message);

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error('[ServiceWorker] Error adding pending message:', error);
        throw error;
    }
}

async function addPendingForm(form) {
    try {
        const db = await openDB();
        const transaction = db.transaction(['pendingForms'], 'readwrite');
        const store = transaction.objectStore('pendingForms');
        const request = store.add(form);

        return new Promise((resolve, reject) => {
            request.onsuccess = () => resolve(request.result);
            request.onerror = () => reject(request.error);
        });
    } catch (error) {
        console.error('[ServiceWorker] Error adding pending form:', error);
        throw error;
    }
}

function getCsrfToken() {
    // Service workers don't have access to DOM
    // CSRF tokens should be handled by the main thread when queuing requests
    return '';
}

// Periodic background sync for real-time updates
self.addEventListener('periodicsync', event => {
    if (event.tag === 'update-notifications') {
        event.waitUntil(updateNotifications());
    }
});

async function updateNotifications() {
    try {
        console.log('[ServiceWorker] Periodic notification update');
        const response = await fetch('/api/notifications/check/');
        if (response.ok) {
            const data = await response.json();
            if (data.has_new) {
                await self.registration.showNotification('New Notifications', {
                    body: `You have ${data.count} new notification${data.count > 1 ? 's' : ''}`,
                    icon: '/static/images/logo.png',
                    badge: '/static/images/logo.png',
                    tag: 'periodic-notifications'
                });
            }
        }
    } catch (error) {
        console.error('[ServiceWorker] Periodic sync error:', error);
    }
}

// Message handling from main thread
self.addEventListener('message', event => {
    if (event.data && event.data.type === 'SKIP_WAITING') {
        self.skipWaiting();
    }
});
