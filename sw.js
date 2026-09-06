/* Service worker mínimo: la web tiene que abrirse en un pabellón sin cobertura.
   Estrategia: se sirve de la caché al instante y se refresca por detrás, así
   que el segundo día ya no espera a la red para nada. */
var CACHE = 'preparacion-fisica-v1';
var ESENCIALES = [
  './', 'index.html',
  'assets/css/estilos.css',
  'assets/js/util.js', 'assets/js/datos.js', 'assets/js/vistas.js', 'assets/js/app.js',
  'data/semanas.json', 'data/ejercicios.json', 'data/protocolos.json', 'data/jugadores.json'
];

self.addEventListener('install', function (ev) {
  ev.waitUntil(caches.open(CACHE).then(function (c) {
    return c.addAll(ESENCIALES);
  }).then(function () { return self.skipWaiting(); }));
});

self.addEventListener('activate', function (ev) {
  ev.waitUntil(caches.keys().then(function (claves) {
    return Promise.all(claves.filter(function (k) { return k !== CACHE; })
      .map(function (k) { return caches.delete(k); }));
  }).then(function () { return self.clients.claim(); }));
});

self.addEventListener('fetch', function (ev) {
  if (ev.request.method !== 'GET') return;
  ev.respondWith(caches.match(ev.request).then(function (guardado) {
    var red = fetch(ev.request).then(function (r) {
      if (r && r.ok) {
        var copia = r.clone();
        caches.open(CACHE).then(function (c) { c.put(ev.request, copia); });
      }
      return r;
    }).catch(function () { return guardado; });
    return guardado || red;
  }));
});
