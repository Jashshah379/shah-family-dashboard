/* Shah Family Wealth Dashboard — service worker.
   Strategy is deliberately NOT "cache forever": holdings data in this app
   changes multiple times a day, so the app shell itself uses network-first
   (always try for the freshest version, only fall back to what's cached
   when there's genuinely no connection). The external CDN dependencies
   (React/ReactDOM at pinned versions, Google Fonts) rarely change, so
   those use cache-first for speed.
*/
const CACHE_NAME = "shah-wealth-v2"; // bumped: v1 could serve stale entries cached before the no-store fix below
const APP_SHELL_URL = self.registration.scope; // the deployed index.html itself

const CDN_HOSTS = ["unpkg.com", "fonts.googleapis.com", "fonts.gstatic.com"];

self.addEventListener("install", function(event) {
  self.skipWaiting();
});

self.addEventListener("activate", function(event) {
  event.waitUntil(
    caches.keys().then(function(names){
      return Promise.all(
        names.filter(function(n){ return n !== CACHE_NAME; })
             .map(function(n){ return caches.delete(n); })
      );
    }).then(function(){ return self.clients.claim(); })
  );
});

/* ── Web Push: receive and display incoming notifications ── */
self.addEventListener("push", function(event) {
  var data = {};
  try { data = event.data ? event.data.json() : {}; } catch(e) {}
  var title = data.title || "Shah Family Dashboard";
  var options = {
    body: data.body || "",
    icon: "icon-192.png",
    badge: "icon-192.png",
    tag: data.tag || undefined, // same tag replaces a still-pending notification rather than stacking
    data: { url: data.url || self.registration.scope },
  };
  event.waitUntil(self.registration.showNotification(title, options));
});

self.addEventListener("notificationclick", function(event) {
  event.notification.close();
  var targetUrl = (event.notification.data && event.notification.data.url) || self.registration.scope;
  event.waitUntil(
    clients.matchAll({ type: "window", includeUncontrolled: true }).then(function(windowClients){
      for (var i = 0; i < windowClients.length; i++) {
        var client = windowClients[i];
        if (client.url.indexOf(self.registration.scope) === 0 && "focus" in client) {
          return client.focus();
        }
      }
      if (clients.openWindow) return clients.openWindow(targetUrl);
    })
  );
});

self.addEventListener("fetch", function(event) {
  var url = new URL(event.request.url);
  if (event.request.method !== "GET") return; // never intercept non-GET

  var isCdn = CDN_HOSTS.indexOf(url.hostname) !== -1;

  if (isCdn) {
    // Cache-first: these are pinned versions, unlikely to change, and
    // serving from cache immediately makes repeat loads much faster.
    event.respondWith(
      caches.match(event.request).then(function(cached){
        if (cached) return cached;
        return fetch(event.request).then(function(res){
          var copy = res.clone();
          caches.open(CACHE_NAME).then(function(c){ c.put(event.request, copy); });
          return res;
        });
      })
    );
    return;
  }

  // Network-first for the app shell itself and any same-origin request:
  // always prefer the live, current data. cache:"no-store" forces this to
  // genuinely bypass the browser's own HTTP cache (not just this service
  // worker's Cache API) — without it, a default fetch() can silently
  // return a cached response per the server's Cache-Control headers, which
  // would defeat the whole point of "network-first" here. Only serve the
  // Cache API copy if the network request genuinely fails (offline, DNS
  // failure, etc).
  event.respondWith(
    fetch(event.request, {cache: "no-store"}).then(function(res){
      var copy = res.clone();
      caches.open(CACHE_NAME).then(function(c){ c.put(event.request, copy); });
      return res;
    }).catch(function(){
      return caches.match(event.request).then(function(cached){
        return cached || caches.match(APP_SHELL_URL);
      });
    })
  );
});
