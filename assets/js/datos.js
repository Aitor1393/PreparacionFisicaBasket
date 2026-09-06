/* El modelo. Carga los datos generados y responde a las preguntas del
   entrenador: qué toca hoy, qué hay esta semana, dónde está la temporada.
   Aquí van las reglas; vistas.js solo pinta.
   Cuelga de window.D y necesita U. */
(function () {
  'use strict';

  var D = {
    temporada: null,   // semanas.json
    ejercicios: null,  // ejercicios.json
    protocolos: null,  // protocolos.json
    jugadores: null,   // jugadores.json
    fichas: {},        // id -> ficha
    cargado: false
  };

  D.cargar = function () {
    var archivos = ['semanas', 'ejercicios', 'protocolos', 'jugadores'];
    return Promise.all(archivos.map(function (n) {
      return fetch('data/' + n + '.json').then(function (r) {
        if (!r.ok) throw new Error('no se ha podido leer data/' + n + '.json');
        return r.json();
      });
    })).then(function (r) {
      D.temporada = r[0];
      D.ejercicios = r[1];
      D.protocolos = r[2];
      D.jugadores = r[3];
      D.ejercicios.fichas.forEach(function (f) { D.fichas[f.id] = f; });
      D.cargado = true;
      return D;
    });
  };

  D.semanas = function () { return D.temporada.semanas; };

  D.semana = function (n) {
    return D.temporada.semanas.filter(function (s) { return s.semana === +n; })[0] || null;
  };

  D.mesociclo = function (id) { return D.temporada.mesociclos[id]; };

  /* La semana que contiene una fecha, de lunes a domingo. */
  D.semanaDeFecha = function (iso) {
    var semanas = D.temporada.semanas;
    for (var i = 0; i < semanas.length; i++) {
      if (iso >= semanas[i].lunes && iso <= U.sumarDias(semanas[i].lunes, 6)) return semanas[i];
    }
    return null;
  };

  D.sesionDeFecha = function (iso) {
    var s = D.semanaDeFecha(iso);
    if (!s) return null;
    return s.sesiones.filter(function (x) { return x.fecha === iso; })[0] || null;
  };

  D.sesion = function (iso) { return D.sesionDeFecha(iso); };

  /* La siguiente sesión a partir de una fecha, mirando como mucho un mes.
     Sirve para que un martes la pantalla de Hoy diga qué viene el miércoles. */
  D.proximaSesion = function (iso) {
    for (var i = 1; i <= 31; i++) {
      var s = D.sesionDeFecha(U.sumarDias(iso, i));
      if (s) return s;
    }
    return null;
  };

  D.dentroDeTemporada = function (iso) {
    var t = D.temporada.meta.temporada;
    return iso >= t.inicio && iso <= t.fin;
  };

  /* Qué pasa un día concreto. Es la pregunta que contesta la pantalla de Hoy.

     Estados: sesion · partido · sinPartido · domingo · descanso · autonomo · fuera */
  D.queToca = function (iso) {
    var dia = U.diaSemana(iso);
    if (!D.dentroDeTemporada(iso)) return { estado: 'fuera', fecha: iso, dia: dia };

    var semana = D.semanaDeFecha(iso);
    if (!semana) return { estado: 'fuera', fecha: iso, dia: dia };

    var base = { fecha: iso, dia: dia, semana: semana };

    if (dia === 'sabado') {
      base.estado = semana.hay_partido ? 'partido' : 'sinPartido';
      return base;
    }
    if (dia === 'domingo') { base.estado = 'domingo'; return base; }

    var sesion = D.sesionDeFecha(iso);
    if (sesion) { base.estado = 'sesion'; base.sesion = sesion; return base; }

    if (semana.formato === 'autonomo') { base.estado = 'autonomo'; return base; }

    base.estado = 'descanso';
    base.proxima = D.proximaSesion(iso);
    return base;
  };

  /* Cuántos días faltan para el partido. El lunes es MD-5, el miércoles MD-3
     y el viernes MD-1, como dice el vocabulario del proyecto. */
  D.md = function (sesion) { return sesion.md; };

  D.plantilla = function (id) { return D.temporada.plantillas[id] || null; };

  D.tramoDolor = function (dolor) {
    var t = D.temporada.protocolo_dolor;
    for (var i = 0; i < t.length; i++) {
      if (dolor >= t[i].min && dolor <= t[i].max) return t[i];
    }
    return null;
  };

  /* ------------------------------------------------------- catálogo */

  D.ficha = function (id) { return D.fichas[id] || null; };

  D.buscarFichas = function (texto, capacidad) {
    var q = U.normalizar(texto || '').trim();
    return D.ejercicios.fichas.filter(function (f) {
      if (capacidad && f.capacidad !== capacidad) return false;
      if (!q) return true;
      return U.normalizar(f.nombre + ' ' + f.como + ' ' + (f.clave || '')).indexOf(q) >= 0;
    });
  };

  /* En cuántas sesiones de la temporada aparece un ejercicio. Es lo que
     convierte una ficha en algo útil: saber si es contenido fijo o anecdótico. */
  D.usosDeFicha = function (id) {
    var usos = [];
    D.temporada.semanas.forEach(function (s) {
      s.sesiones.forEach(function (ses) {
        var dosis = [];
        ses.bloques.forEach(function (b) {
          (b.ejercicios || []).forEach(function (e) {
            if (e.ficha === id) dosis.push(e.texto);
          });
        });
        if (dosis.length) usos.push({ sesion: ses, semana: s, dosis: dosis });
      });
    });
    return usos;
  };

  D.rutina = function (id) { return D.ejercicios.rutinas[id] || null; };

  window.D = D;
}());
