// Service-Worker: macht die Seite installierbar & offline-fähig.
// Strategie: Navigation network-first (immer frische Prognosen, wenn online),
// statische Dateien cache-first.
const CACHE = 'tipp-v1';
const SHELL = ['index.html', 'manifest.webmanifest',
               'icons/icon-192.png', 'icons/icon-512.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((ks) => Promise.all(ks.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.mode === 'navigate') {
    e.respondWith(
      fetch(req).then((r) => {
        const copy = r.clone();
        caches.open(CACHE).then((c) => c.put(req, copy));
        return r;
      }).catch(() => caches.match(req).then((m) => m || caches.match('index.html')))
    );
    return;
  }
  e.respondWith(caches.match(req).then((c) => c || fetch(req)));
});
