const C="sedori-map-202611111541";
const ASSETS=["./", "./index.html", "./guide.html", "./leaflet.js", "./leaflet.css", "./data/stores.json", "./manifest.webmanifest", "./icon-180.png", "./icon-192.png", "./icon-512.png", "./icon-512-maskable.png"];
self.addEventListener("install",function(e){e.waitUntil(caches.open(C).then(function(c){return c.addAll(ASSETS)}).then(function(){return self.skipWaiting()}))});
self.addEventListener("activate",function(e){e.waitUntil(caches.keys().then(function(ks){return Promise.all(ks.map(function(k){if(k!==C)return caches.delete(k)}))}).then(function(){return self.clients.claim()}))});
self.addEventListener("fetch",function(e){
  if(e.request.method!=="GET")return;
  var u=new URL(e.request.url); if(u.origin!==location.origin) return;
  var isPage=e.request.mode==="navigate"||/(\/|index\.html)$/.test(u.pathname);
  if(isPage){
    e.respondWith(fetch(e.request).then(function(resp){var cp=resp.clone();caches.open(C).then(function(c){c.put(e.request,cp)});return resp}).catch(function(){return caches.match(e.request).then(function(r){return r||caches.match("./index.html")})}));
  }else{
    e.respondWith(caches.match(e.request).then(function(r){return r||fetch(e.request).then(function(resp){var cp=resp.clone();caches.open(C).then(function(c){c.put(e.request,cp)});return resp})}));
  }
});
