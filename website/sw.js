/* Service Worker for binateam.site. The build script fills in VERSION and PRECACHE.
   Pages: network first, then the cached copy, then offline.html. Files: cache first, refreshed in the background.
   A new build gets a new VERSION, so the next visit installs fresh copies and removes the old cache. */
var VERSION = "__VERSION__";
var CACHE = "bina-" + VERSION;
var PRECACHE = __PRECACHE__;

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(CACHE).then(function (cache) {
      return Promise.all(PRECACHE.map(function (url) {
        return fetch(new Request(url, { cache: "reload" })).then(function (res) {
          if (res.ok) return cache.put(url, res);
        }).catch(function () {});
      }));
    }).then(function () { return self.skipWaiting(); })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.filter(function (k) { return k.indexOf("bina-") === 0 && k !== CACHE; })
        .map(function (k) { return caches.delete(k); }));
    }).then(function () { return self.clients.claim(); })
  );
});

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;
  var url = new URL(req.url);
  if (url.origin !== self.location.origin) return;

  if (req.mode === "navigate") {
    event.respondWith(
      fetch(req).then(function (res) {
        if (res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(url.pathname, copy); });
        }
        return res;
      }).catch(function () {
        return caches.match(url.pathname, { ignoreSearch: true }).then(function (hit) {
          return hit || caches.match("/offline.html");
        });
      })
    );
    return;
  }

  event.respondWith(
    caches.match(req, { ignoreSearch: true }).then(function (hit) {
      var refresh = fetch(req).then(function (res) {
        if (res.ok) {
          var copy = res.clone();
          caches.open(CACHE).then(function (c) { c.put(req, copy); });
        }
        return res;
      }).catch(function () { return hit; });
      return hit || refresh;
    })
  );
});
