const CACHE_NAME = 'fixjeict-v1';
const STATIC_CACHE = 'fixjeict-static-v1';

const STATIC_ASSETS = [
    '/',
    '/static/css/style.css',
    '/static/manifest.json',
    '/static/images/icon-192.png',
    '/static/images/icon-512.png',
    '/static/images/favicon.svg'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
    event.waitUntil(
        caches.open(STATIC_CACHE)
            .then((cache) => cache.addAll(STATIC_ASSETS))
            .then(() => self.skipWaiting())
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames.map((cacheName) => {
                        if (cacheName !== STATIC_CACHE && cacheName !== CACHE_NAME) {
                            return caches.delete(cacheName);
                        }
                    })
                );
            })
            .then(() => self.clients.claim())
    );
});

// Fetch event - cache first for static, network first for HTML
self.addEventListener('fetch', (event) => {
    const url = new URL(event.request.url);

    // Cache first for static assets
    if (url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(event.request)
                .then((cachedResponse) => {
                    if (cachedResponse) {
                        return cachedResponse;
                    }
                    return fetch(event.request)
                        .then((response) => {
                            return caches.open(STATIC_CACHE)
                                .then((cache) => {
                                    cache.put(event.request, response.clone());
                                    return response;
                                });
                        });
                })
        );
        return;
    }

    // Network first for HTML pages
    if (url.pathname.startsWith('/') || url.pathname.startsWith('/tickets/') || url.pathname.startsWith('/dashboard')) {
        event.respondWith(
            fetch(event.request)
                .then((response) => {
                    const responseClone = response.clone();
                    caches.open(CACHE_NAME)
                        .then((cache) => {
                            cache.put(event.request, responseClone);
                        });
                    return response;
                })
                .catch(() => {
                    return caches.match(event.request);
                })
        );
        return;
    }

    // Default: network first, fallback to cache
    event.respondWith(
        fetch(event.request)
            .then((response) => {
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then((cache) => {
                        cache.put(event.request, responseClone);
                    });
                return response;
            })
            .catch(() => {
                return caches.match(event.request);
            })
    );
});

// Background sync for offline actions (optional enhancement)
self.addEventListener('sync', (event) => {
    if (event.tag === 'sync-tickets') {
        event.waitUntil(syncTickets());
    }
});

function syncTickets() {
    // Implement background sync logic here
    return Promise.resolve();
}
