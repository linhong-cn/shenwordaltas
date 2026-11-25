/* Grade 1-6 Atlas offline cache: app shell network-first, everything else cache-first. */
const VERSION = "atlas-g1to6-v7";
const SHELL = `${VERSION}-shell`;
const MEDIA = `${VERSION}-media`;

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) => Promise.all(keys.filter((k) => !k.startsWith(VERSION)).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

async function trim(name, max) {
  const cache = await caches.open(name);
  const keys = await cache.keys();
  for (let i = 0; i < keys.length - max; i++) await cache.delete(keys[i]);
}

self.addEventListener("fetch", (event) => {
  const req = event.request;
  if (req.method !== "GET" || req.headers.has("range")) return;
  const url = new URL(req.url);
  if (url.origin !== location.origin) return;
  const isNavigate = req.mode === "navigate";
  const isData = url.pathname.endsWith(".json");
  if (isNavigate || isData) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          // A SPA fallback (text/html) must never be cached or served as JSON data.
          const okType = !isData || (res.headers.get("content-type") || "").includes("json");
          if (res.ok && okType) caches.open(SHELL).then((c) => c.put(req, res.clone()));
          return res;
        })
        .catch(async () => {
          const hit = await caches.match(req);
          if (hit) return hit;
          if (isNavigate) {
            const shell = await caches.match(new URL("./", self.registration.scope).href);
            if (shell) return shell;
          }
          return new Response("", { status: 503, statusText: "offline" });
        }),
    );
    return;
  }
  event.respondWith(
    caches.match(req).then(
      (hit) =>
        hit ||
        fetch(req).then((res) => {
          if (res.ok && res.type === "basic") {
            const copy = res.clone();
            const name = /\/atlas\/g\d+\/(img|thumb|audio)\//.test(url.pathname) ? MEDIA : SHELL;
            caches.open(name).then((c) => c.put(req, copy)).then(() => name === MEDIA && trim(MEDIA, 1500));
          }
          return res;
        }),
    ),
  );
});
