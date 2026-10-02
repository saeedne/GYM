const CACHE_NAME = "gym-manager-shell-v5";
const OFFLINE_URL = "/static/offline.html";
self.addEventListener("install", event => {
  event.waitUntil(caches.open(CACHE_NAME).then(cache => cache.addAll([
    OFFLINE_URL,
    "/static/css/app.css?v=20260929f",
    "/static/css/mobile.css?v=20260930a",
    "/static/js/app.js?v=20260929f",
    "/static/vendor/jquery-3.7.1.min.js",
    "/static/vendor/persian-date-1.1.0.min.js",
    "/static/vendor/persian-datepicker-1.2.0.min.js",
    "/static/vendor/persian-datepicker-1.2.0.min.css",
    "/static/images/gym-icon.svg",
    "/static/images/gym-icon-192.png",
    "/static/images/gym-icon-512.png",
    "/static/manifest.webmanifest"
  ])).then(() => self.skipWaiting()));
});
self.addEventListener("activate", event => {
  event.waitUntil(caches.keys().then(keys => Promise.all(keys.filter(key => key !== CACHE_NAME).map(key => caches.delete(key)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", event => {
  const request = event.request;
  const url = new URL(request.url);
  if (request.method !== "GET" || url.origin !== self.location.origin) return;
  if (url.pathname.startsWith("/static/")) {
    event.respondWith(caches.match(request).then(cached => cached || fetch(request).then(response => {
      if (response.ok) caches.open(CACHE_NAME).then(cache => cache.put(request, response.clone()));
      return response;
    })));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(fetch(request).catch(() => caches.match(OFFLINE_URL)));
  }
});
