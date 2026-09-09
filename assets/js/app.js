/* Rutas, eventos y arranque. Cuelga de window.App y necesita U, D y V. */
(function () {
  'use strict';

  var App = {
    estado: { texto: '', capacidad: '' }
  };

  var RUTAS = [
    [/^\/?$|^\/hoy$/, function () { return V.hoy(D.queToca(U.hoyIso())); }],
    [/^\/calendario$/, function () { return V.calendario(); }],
    [/^\/semana\/(\d+)$/, function (m) { return V.semana(m[1]); }],
    [/^\/sesion\/(\d{4}-\d{2}-\d{2})$/, function (m) { return V.sesion(m[1]); }],
    [/^\/plantilla\/([\w-]+)$/, function (m) { return V.plantilla(m[1]); }],
    [/^\/ejercicios$/, function () { return V.ejercicios(App.estado); }],
    [/^\/ejercicio\/([\w-]+)$/, function (m) { return V.ficha(m[1]); }],
    [/^\/rutinas$/, function () { return V.rutinas(); }],
    [/^\/rutina\/([\w-]+)$/, function (m) { return V.rutina(m[1]); }],
    [/^\/protocolos$/, function () { return V.protocolos(); }],
    [/^\/lesion\/([\w-]+)$/, function (m) { return V.lesion(m[1]); }],
    [/^\/jugadores$/, function () { return V.jugadores(); }]
  ];

  function ruta() {
    return decodeURIComponent(location.hash.replace(/^#/, '')) || '/hoy';
  }

  App.pintar = function () {
    var r = ruta(), app = U.$('#app');
    for (var i = 0; i < RUTAS.length; i++) {
      var m = r.match(RUTAS[i][0]);
      if (m) {
        try {
          app.innerHTML = RUTAS[i][1](m);
        } catch (e) {
          app.innerHTML = '<h1>Algo ha fallado al pintar</h1><p class="silencio">' +
            U.esc(e.message) + '</p>';
          throw e;
        }
        App.marcarNav(r);
        // Al cambiar de pantalla se vuelve arriba, salvo al teclear en el buscador.
        if (!App.sinSubir) window.scrollTo(0, 0);
        App.sinSubir = false;
        return;
      }
    }
    app.innerHTML = '<h1>Esa página no existe</h1><p><a href="#/hoy">Volver a Hoy</a></p>';
  };

  App.marcarNav = function (r) {
    var raiz = '/' + (r.split('/')[1] || 'hoy');
    var equivalencias = {
      '/semana': '/calendario', '/sesion': '/hoy', '/plantilla': '/hoy',
      '/ejercicio': '/ejercicios', '/rutina': '/ejercicios',
      '/rutinas': '/ejercicios', '/lesion': '/protocolos'
    };
    var activa = equivalencias[raiz] || raiz;
    U.$$('.nav a').forEach(function (a) {
      var suya = a.getAttribute('href').replace('#', '');
      if (suya === activa) a.setAttribute('aria-current', 'page');
      else a.removeAttribute('aria-current');
    });
  };

  /* ------------------------------------------------------------------ tema */

  App.tema = function (valor) {
    if (valor) {
      document.documentElement.setAttribute('data-tema', valor);
      U.guardar('tema', valor);
    }
    return document.documentElement.getAttribute('data-tema');
  };

  App.alternarTema = function () {
    var oscuro = App.tema() === 'oscuro' ||
      (!App.tema() && window.matchMedia('(prefers-color-scheme: dark)').matches);
    App.tema(oscuro ? 'claro' : 'oscuro');
  };

  /* ---------------------------------------------------------------- eventos */

  function eventos() {
    window.addEventListener('hashchange', App.pintar);

    U.$('#btnTema').addEventListener('click', App.alternarTema);

    // Delegación: las vistas se repintan enteras, así que no se enganchan
    // escuchadores a nada que se acabe de crear.
    document.addEventListener('click', function (ev) {
      var boton = ev.target.closest('[data-accion="imprimir"]');
      if (boton) { window.print(); return; }

      var filtro = ev.target.closest('.filtro[data-capacidad]');
      if (filtro) {
        App.estado.capacidad = filtro.getAttribute('data-capacidad');
        App.sinSubir = true;
        App.pintar();
      }
    });

    document.addEventListener('input', function (ev) {
      if (ev.target.id !== 'buscarEjercicio') return;
      App.estado.texto = ev.target.value;
      App.sinSubir = true;
      var pos = ev.target.selectionStart;
      App.pintar();
      var campo = U.$('#buscarEjercicio');
      if (campo) { campo.focus(); campo.setSelectionRange(pos, pos); }
    });
  }

  /* ---------------------------------------------------------------- arranque */

  App.arrancar = function () {
    var guardado = U.leer('tema', null);
    if (guardado) App.tema(guardado);

    D.cargar().then(function () {
      eventos();
      App.pintar();
      App.pie();
    }).catch(function (e) {
      U.$('#app').innerHTML = '<h1>No se han podido cargar los datos</h1>' +
        '<p class="silencio">' + U.esc(e.message) + '</p>' +
        '<p>Si has abierto el archivo directamente desde el disco, el navegador ' +
        'bloquea la lectura de <code>data/</code>. Hace falta servirlo, por ejemplo con ' +
        '<code>python3 -m http.server</code>.</p>';
    });

    if ('serviceWorker' in navigator && location.protocol !== 'file:') {
      navigator.serviceWorker.register('sw.js').catch(function () {});
    }
  };

  App.pie = function () {
    var t = D.temporada.meta.temporada;
    U.$('#pieDatos').textContent = t.microciclos + ' microciclos · ' +
      D.temporada.semanas.reduce(function (n, s) { return n + s.sesiones.length; }, 0) +
      ' sesiones · ' + D.ejercicios.fichas.length + ' ejercicios';
  };

  window.App = App;
  document.addEventListener('DOMContentLoaded', App.arrancar);
}());
