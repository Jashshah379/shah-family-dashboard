/* Shah Family Wealth Dashboard — service worker.
   Strategy is deliberately NOT "cache forever": holdings data in this app
   changes multiple times a day, so the app shell itself uses network-first
   (always try for the freshest version, only fall back to what's cached
   when there's genuinely no connection). The external CDN dependencies
   (React/ReactDOM at pinned versions, Google Fonts) rarely change, so
   those use cache-first for speed.
*/
const CACHE_NAME = "shah-wealth-v1";
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
  // always prefer the live, current data. Only serve the cached copy if
  // the network request genuinely fails (offline, DNS failure, etc).
  event.respondWith(
    fetch(event.request).then(function(res){
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
