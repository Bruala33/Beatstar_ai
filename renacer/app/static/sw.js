const CACHE_NAME = 'beatstar-v1';
const STATIC_ASSETS = [
  '/',
  '/static/style.css',
  '/static/game.js',
  '/static/manifest.json',
  '/static/icon.svg'
];

self.addEventListener('install', (e) => {
  e.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((k) => {
          if (k !== CACHE_NAME) return caches.delete(k);
        })
      );
    })
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  // Pass through dynamic YouTube and API requests directly
  if (e.request.url.includes('/api/') || e.request.url.includes('youtube') || e.request.url.includes('ytimg')) {
    return;
  }
  e.respondWith(
    caches.match(e.request).then((res) => {
      return res || fetch(e.request);
    })
  );
});
