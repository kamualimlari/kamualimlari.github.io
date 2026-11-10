// Kabuk önbellekte, veri her zaman önce ağdan (güncel kalsın), ağ yoksa son kopya.
const KABUK = "kabuk-v1";
self.addEventListener("install", (e) => {
  e.waitUntil(caches.open(KABUK).then((c) => c.addAll(["./", "manifest.webmanifest", "icons/icon-192.png"])).then(() => self.skipWaiting()));
});
self.addEventListener("activate", (e) => {
  e.waitUntil(caches.keys().then((k) => Promise.all(k.filter((x) => x !== KABUK).map((x) => caches.delete(x)))).then(() => self.clients.claim()));
});
self.addEventListener("fetch", (e) => {
  if (e.request.method !== "GET" || new URL(e.request.url).origin !== location.origin) return;
  e.respondWith(
    fetch(e.request).then((r) => {
      const kopya = r.clone();
      caches.open(KABUK).then((c) => c.put(e.request, kopya));
      return r;
    }).catch(() => caches.match(e.request).then((m) => m || caches.match("./")))
  );
});
