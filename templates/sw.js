// ICG service worker — bump CACHE_NAME on any caching strategy change so old
// caches get evicted on activate.
const CACHE_NAME = 'icg-shell-v1';

// Pre-cache the bare minimum so the app can boot offline (just the start URL).
// We deliberately do NOT pre-cache /static/ assets — they're cached on first
// fetch via the runtime handler below, which avoids stale assets after deploy.
const PRECACHE_URLS = ['/'];

self.addEventListener('install', (event) => {
    event.waitUntil(
        caches
            .open(CACHE_NAME)
            .then((cache) => cache.addAll(PRECACHE_URLS))
            .then(() => self.skipWaiting())
    );
});

self.addEventListener('activate', (event) => {
    event.waitUntil(
        caches
            .keys()
            .then((keys) =>
                Promise.all(
                    keys.filter((k) => k !== CACHE_NAME).map((k) => caches.delete(k))
                )
            )
            .then(() => self.clients.claim())
    );
});

self.addEventListener('fetch', (event) => {
    const request = event.request;
    if (request.method !== 'GET') return;

    const url = new URL(request.url);

    // Never intercept admin, auth, or htmx flows — those need fresh network.
    if (
        url.pathname.startsWith('/admin/') ||
        url.pathname.startsWith('/accounts/') ||
        request.headers.get('HX-Request')
    ) {
        return;
    }

    // HTML pages → network-first, fall back to cached / offline shell.
    const isHtml =
        request.mode === 'navigate' ||
        (request.headers.get('accept') || '').includes('text/html');

    if (isHtml) {
        event.respondWith(
            fetch(request)
                .then((response) => {
                    // Cache successful navigations so they can be served offline next time.
                    if (response && response.status === 200 && response.type === 'basic') {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((c) => c.put(request, clone));
                    }
                    return response;
                })
                .catch(() =>
                    caches.match(request).then((cached) => cached || caches.match('/'))
                )
        );
        return;
    }

    // Same-origin static assets → cache-first, populate on miss.
    if (url.origin === self.location.origin && url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request).then((cached) => {
                if (cached) return cached;
                return fetch(request).then((response) => {
                    if (response && response.status === 200) {
                        const clone = response.clone();
                        caches.open(CACHE_NAME).then((c) => c.put(request, clone));
                    }
                    return response;
                });
            })
        );
    }
    // Other requests: let the browser handle them.
});
