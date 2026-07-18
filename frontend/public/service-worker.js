/* Wren AI — PWA Service Worker */
const CACHE = "wren-v1";
const ASSETS = ["/", "/manifest.json"];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(CACHE).then((cache) => cache.addAll(ASSETS)),
  );
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))),
    ),
  );
  self.clients.claim();
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;

  const url = new URL(request.url);

  // Never cache API calls, WebSocket upgrades, or event streams
  if (
    url.pathname.startsWith("/api/") ||
    url.pathname.startsWith("/ws") ||
    url.pathname.startsWith("/socket.io") ||
    url.pathname.startsWith("/orchestration")
  ) {
    return;
  }

  // Only cache same-origin static assets
  if (url.origin !== self.location.origin) return;

  // Cache-first for static assets, network-first for everything else
  const isStatic =
    url.pathname.startsWith("/assets/") ||
    url.pathname === "/" ||
    url.pathname === "/manifest.json";

  if (isStatic) {
    event.respondWith(
      caches.match(request).then((cached) => cached || fetch(request).then((res) => {
        const clone = res.clone();
        caches.open(CACHE).then((cache) => cache.put(request, clone));
        return res;
      })),
    );
  } else {
    event.respondWith(
      fetch(request)
        .then((res) => {
          const clone = res.clone();
          caches.open(CACHE).then((cache) => cache.put(request, clone));
          return res;
        })
        .catch(() => caches.match(request)),
    );
  }
});
