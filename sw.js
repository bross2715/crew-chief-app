// Network first so a new data.json shows up right away. The cache is only the offline fallback.
var C = 'cchq-v10';
self.addEventListener('install', function (e) {
  e.waitUntil(caches.open(C).then(function (c) {
    return c.addAll(['./', 'index.html', 'maps.json', 'data.json', 'manifest.webmanifest', 'icon-192.png', 'avatar.png']);
  }));
  self.skipWaiting();
});
self.addEventListener('activate', function (e) {
  e.waitUntil(caches.keys().then(function (ks) {
    return Promise.all(ks.filter(function (k) { return k !== C; }).map(function (k) { return caches.delete(k); }));
  }));
  self.clients.claim();
});
self.addEventListener('fetch', function (e) {
  if (e.request.method !== 'GET') return;
  var u = new URL(e.request.url);
  if (u.origin !== location.origin) return;
  e.respondWith(
    fetch(e.request).then(function (r) {
      var cp = r.clone();
      caches.open(C).then(function (c) { c.put(e.request, cp); });
      return r;
    }).catch(function () { return caches.match(e.request, { ignoreSearch: true }); })
  );
});
