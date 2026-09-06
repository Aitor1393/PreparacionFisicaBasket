/* Genera el HTML de cada pantalla. No decide nada: todo lo que hay que
   calcular está en datos.js. Cuelga de window.V y necesita U y D. */
(function () {
  'use strict';

  var V = {};
  var COLOR_TIPO = {
    construccion: 'var(--construccion)', mantenimiento: 'var(--mantenimiento)',
    paron: 'var(--paron)', final: 'var(--final)'
  };
  var NOMBRE_TIPO = {
    construccion: 'Construcción de fuerza', mantenimiento: 'Mantenimiento en competición',
    paron: 'Parón o trabajo autónomo', final: 'Fase final'
  };

  /* --------------------------------------------------------------- piezas */

  function eti(texto, clase) {
    return '<span class="eti ' + (clase || '') + '">' + U.esc(texto) + '</span>';
  }

  function cifra(valor, etiqueta) {
    return '<div class="cifra"><div class="cifra__valor">' + U.esc(valor) +
      '</div><div class="cifra__etiqueta">' + U.esc(etiqueta) + '</div></div>';
  }

  function nombreSemana(s) {
    return s.microciclo ? s.microciclo : 'Semana ' + s.semana;
  }

  V.nombreSemana = nombreSemana;

  function ejercicio(e) {
    if (!e.ficha) return '<li><span class="sin-ficha">' + U.esc(e.texto) + '</span></li>';
    return '<li><a href="#/ejercicio/' + U.esc(e.ficha) + '">' + U.esc(e.texto) + '</a></li>';
  }

  function bloque(b) {
    var h = '<div class="bloque"><div class="bloque__cabecera">' +
      '<span class="bloque__min">' + (b.min ? b.min + "'" : '') + '</span>' +
      '<span class="bloque__nombre">' + U.esc(b.nombre || b.texto) + '</span>';
    if (b.contactos) h += eti(b.contactos + ' contactos', 'eti--gris');
    h += '</div>';
    if (b.detalle) h += '<p class="bloque__detalle">' + U.esc(b.detalle) + '</p>';
    if (b.ejercicios && b.ejercicios.length) {
      h += '<ul class="ejercicios">' + b.ejercicios.map(ejercicio).join('') + '</ul>';
    }
    if (b.rutina) {
      h += '<p class="remite">Rutina cronometrada: <a href="#/rutina/' + U.esc(b.rutina) +
        '">' + U.esc(D.rutina(b.rutina).titulo) + '</a></p>';
    }
    if (b.remite_a) {
      h += '<p class="remite">El documento no repite el detalle aquí. Es el bloque de la ' +
        'plantilla <a href="#/plantilla/' + U.esc(b.remite_a) + '">' + U.esc(b.remite_a) +
        '</a>.</p>';
    }
    return h + '</div>';
  }

  V.bloques = function (bloques) {
    return '<div class="tarjeta">' + bloques.map(bloque).join('') + '</div>';
  };

  /* Varios avisos van en un solo recuadro con lista: cuatro cajas seguidas
     ocupan media pantalla de móvil y hacen que se pierda de vista la sesión. */
  function avisos(lista, clase, titulo) {
    if (!lista || !lista.length) return '';
    var caja = '<div class="caja ' + (clase || 'caja--aviso') + '">';
    if (lista.length === 1) return caja + '<p>' + U.negritas(lista[0]) + '</p></div>';
    if (titulo) caja += '<h3>' + U.esc(titulo) + '</h3>';
    return caja + '<ul>' + lista.map(function (t) {
      return '<li>' + U.negritas(t) + '</li>';
    }).join('') + '</ul></div>';
  }

  V.avisos = avisos;

  /* ------------------------------------------------------------------ hoy */

  V.hoy = function (que) {
    if (que.estado === 'fuera') return V.fueraDeTemporada(que);

    var s = que.semana;
    var h = '<div class="hoy__cabecera">' +
      '<div class="hoy__dia">' + U.esc(U.fechaLarga(que.fecha)) + '</div>';

    if (que.estado === 'sesion') {
      h += '<h1 class="hoy__titulo">' + U.esc(que.sesion.titulo) + '</h1>';
    } else if (que.estado === 'partido') {
      h += '<h1 class="hoy__titulo">Partido · ' + U.esc(s.jornada) + '</h1>';
    } else if (que.estado === 'sinPartido') {
      h += '<h1 class="hoy__titulo">Fin de semana sin partido</h1>';
    } else if (que.estado === 'domingo') {
      h += '<h1 class="hoy__titulo">Domingo · rutina de regeneración</h1>';
    } else if (que.estado === 'autonomo') {
      h += '<h1 class="hoy__titulo">Semana de trabajo autónomo</h1>';
    } else {
      h += '<h1 class="hoy__titulo">Hoy no hay sesión</h1>';
    }
    h += '</div>';

    h += '<div class="cifras">' +
      cifra(nombreSemana(s), D.mesociclo(s.mesociclo).nombre) +
      cifra(s.carga + '/10', 'Carga de la semana') +
      cifra(s.contactos_pliometria, 'Contactos') +
      cifra(s.hay_partido ? s.jornada : '—', s.hay_partido ? 'Sábado' : 'Sin partido') +
      '</div>';

    if (que.estado === 'sesion') {
      h += V.sesionCuerpo(que.sesion, s);
    } else if (que.estado === 'domingo') {
      h += '<p class="sub">El día después del partido. Está pensada para hacerla en casa.</p>' +
        '<p><a class="btn btn--principal" href="#/jugadores">Ver la rutina del domingo</a></p>';
    } else if (que.estado === 'autonomo') {
      h += '<p class="sub">' + U.esc(s.plan_autonomo || 'No hay sesión presencial esta semana.') +
        '</p><p><a class="btn btn--principal" href="#/jugadores">Ver el plan del jugador</a></p>';
    } else if (que.estado === 'partido' || que.estado === 'sinPartido') {
      h += '<p class="sub">Hoy no hay sesión de física. La semana es esta:</p>' + V.resumenSemana(s);
    } else if (que.proxima) {
      h += '<p class="sub">La siguiente es el ' + U.esc(U.fechaLarga(que.proxima.fecha)) + '.</p>' +
        V.sesionCuerpo(que.proxima, D.semana(que.proxima.semana));
    }

    h += '<p class="no-imprimir"><a href="#/semana/' + s.semana + '">Ver la semana completa →</a></p>';
    return h;
  };

  V.fueraDeTemporada = function (que) {
    var t = D.temporada.meta.temporada;
    return '<h1>Fuera de temporada</h1>' +
      '<p class="sub">Hoy es ' + U.esc(U.fechaLarga(que.fecha)) + '. La temporada va del ' +
      U.esc(U.fechaLarga(t.inicio)) + ' al ' + U.esc(U.fechaLarga(t.fin)) + '.</p>' +
      V.calendario();
  };

  /* -------------------------------------------------------------- sesión */

  V.sesionCuerpo = function (ses, semana) {
    var h = '<div class="etis">' +
      eti(ses.minutos + ' minutos') +
      eti(ses.md, 'eti--gris') +
      (ses.plantilla ? eti('Plantilla ' + ses.plantilla, 'eti--gris') : '') +
      (ses.estado === 'plantilla' ? eti('Se resuelve por plantilla', 'eti--gris') : '') +
      '</div>';

    // Las series NO se calculan aquí. La regla de la carga es de M4-M5 y en M7
    // no vale: allí son 2 series salvo el curl nórdico. Cada sesión trae ya
    // escrito su ajuste desde su propia fuente, y es lo único que se enseña.
    h += avisos(ses.ajustes, 'caja--acento', 'Cómo se ejecuta esta semana');
    h += V.bloques(ses.bloques);
    h += avisos(ses.notas);
    h += '<p class="pequeno silencio">Fuente: ' + U.esc(ses.origen.archivo) +
      ' · ' + U.esc(ses.origen.seccion) + '</p>';
    return h;
  };

  V.sesion = function (iso) {
    var ses = D.sesion(iso);
    if (!ses) return '<h1>No hay sesión ese día</h1><p><a href="#/calendario">Ir al calendario</a></p>';
    var semana = D.semana(ses.semana);
    return '<p class="pequeno no-imprimir"><a href="#/semana/' + semana.semana + '">← ' +
      U.esc(nombreSemana(semana)) + '</a></p>' +
      '<h1>' + U.esc(ses.titulo) + '</h1>' +
      '<p class="sub">' + U.esc(U.fechaLarga(ses.fecha)) + ' · ' +
      U.esc(D.mesociclo(semana.mesociclo).nombre) + ' · carga ' + semana.carga + '</p>' +
      '<p class="no-imprimir"><button class="btn" data-accion="imprimir">Imprimir esta sesión</button></p>' +
      V.sesionCuerpo(ses, semana);
  };

  V.plantilla = function (id) {
    var p = D.plantilla(id);
    if (!p) return '<h1>No existe esa plantilla</h1>';
    return '<h1>Plantilla ' + U.esc(p.id) + '</h1>' +
      '<p class="sub">' + U.esc(p.nombre) + ' · ' + U.esc(p.dia) + ' · ' + p.minutos + ' minutos</p>' +
      V.bloques(p.bloques) +
      '<p class="pequeno silencio">Fuente: ' + U.esc(p.origen.archivo) + ' · ' +
      U.esc(p.origen.seccion) + '</p>';
  };

  /* ------------------------------------------------------------ microciclo */

  V.resumenSemana = function (s) {
    if (!s.sesiones.length) {
      return '<div class="caja caja--aviso"><p>Semana sin sesión presencial. ' +
        U.esc(s.plan_autonomo || '') + '</p></div>';
    }
    return '<div class="lista">' + s.sesiones.map(function (ses) {
      var resumen = ses.bloques.filter(function (b) { return b.nombre; })
        .map(function (b) { return b.nombre; }).join(' · ');
      return '<a class="enlace-tarjeta" href="#/sesion/' + ses.fecha + '">' +
        '<div class="enlace-tarjeta__titulo">' + U.esc(ses.titulo) + '</div>' +
        '<div class="enlace-tarjeta__pie">' + U.esc(U.fechaCorta(ses.fecha)) + ' · ' +
        ses.minutos + "' · " + U.esc(ses.md) + ' · ' + U.esc(resumen) + '</div></a>';
    }).join('') + '</div>';
  };

  V.semana = function (n) {
    var s = D.semana(n);
    if (!s) return '<h1>No existe esa semana</h1>';
    var m = D.mesociclo(s.mesociclo);
    var h = '<p class="pequeno no-imprimir"><a href="#/calendario">← Calendario</a></p>' +
      '<h1>' + U.esc(nombreSemana(s)) + '</h1>' +
      '<p class="sub">' + U.esc(U.rango(s.lunes, U.sumarDias(s.lunes, 6))) + ' · ' +
      U.esc(s.mesociclo + ' ' + m.nombre) + '</p>' +
      '<div class="cifras">' +
      cifra(s.carga + '/10', 'Carga') +
      cifra(s.contactos_pliometria, 'Contactos') +
      cifra(s.hay_partido ? s.jornada : 'Libre', 'Sábado ' + U.fechaCorta(s.sabado)) +
      cifra('Semana ' + s.semana, 'de 39') +
      '</div>';

    h += V.resumenSemana(s);
    if (s.variantes && s.variantes.length) {
      h += '<h2>Otra versión de la semana</h2>' + s.variantes.map(function (v) {
        return '<div class="caja caja--aviso"><p><strong>' + U.esc(v.titulo) + '</strong></p>' +
          '<p>' + U.esc(v.sesiones.join(' · ')) + '</p>' +
          v.texto.map(function (t) { return '<p>' + U.negritas(t) + '</p>'; }).join('') + '</div>';
      }).join('');
    }
    h += avisos(s.notas);
    if (s.origen) {
      h += '<p class="pequeno silencio">Fuente: ' + U.esc(s.origen.archivo) + ' · ' +
        U.esc(s.origen.seccion) + '</p>';
    }
    return h;
  };

  /* ------------------------------------------------------------- calendario */

  V.calendario = function () {
    var hoy = U.hoyIso();
    var actual = D.semanaDeFecha(hoy);
    var h = '<h1>Calendario</h1><p class="sub">Las 39 semanas de la temporada. ' +
      'La altura de la barra es la carga; el color, el tipo de bloque.</p>';

    h += '<div class="leyenda">' + Object.keys(NOMBRE_TIPO).map(function (t) {
      return '<span><i style="background:' + COLOR_TIPO[t] + '"></i>' + U.esc(NOMBRE_TIPO[t]) + '</span>';
    }).join('') + '</div>';

    var meso = null;
    h += '<div class="cal">';
    D.semanas().forEach(function (s) {
      if (s.mesociclo !== meso) {
        meso = s.mesociclo;
        h += '<div class="cal__grupo">' + U.esc(meso + ' · ' + D.mesociclo(meso).nombre) + '</div>';
      }
      var esHoy = actual && actual.semana === s.semana;
      h += '<a class="cal__fila' + (esHoy ? ' cal__fila--hoy' : '') + '" href="#/semana/' + s.semana + '">' +
        '<span class="cal__num">' + s.semana + '</span>' +
        '<span class="cal__fecha">' + U.esc(U.fechaCorta(s.lunes)) + '</span>' +
        '<span class="cal__barra"><span class="cal__relleno" style="width:' + (s.carga * 10) +
        '%;background:' + COLOR_TIPO[s.tipo] + ';opacity:.35"></span>' +
        '<span class="cal__carga">' + s.carga + (s.microciclo ? ' · ' + U.esc(s.microciclo) : '') +
        '</span></span>' +
        '<span class="cal__jornada"' + (s.hay_partido ? '' : ' class="silencio"') + '>' +
        U.esc(s.hay_partido ? s.jornada : '—') + '</span></a>';
    });
    h += '</div>';
    h += '<p class="pequeno silencio">Las semanas sin partido son las de carga: en la temporada ' +
      'solo hay nueve de treinta y nueve.</p>';
    return h;
  };

  /* ------------------------------------------------------------- ejercicios */

  V.ejercicios = function (estado) {
    var caps = D.ejercicios.capacidades;
    var h = '<h1>Ejercicios</h1><p class="sub">' + D.ejercicios.fichas.length +
      ' fichas: cómo se hace, la clave técnica y el error que más se repite.</p>' +
      '<p class="no-imprimir"><input class="buscador" id="buscarEjercicio" type="search" ' +
      'placeholder="Buscar un ejercicio…" value="' + U.esc(estado.texto || '') +
      '" autocomplete="off"></p>' +
      '<div class="filtros no-imprimir"><button class="filtro" data-capacidad="" aria-pressed="' +
      (!estado.capacidad) + '">Todas</button>';
    Object.keys(caps).forEach(function (c) {
      h += '<button class="filtro" data-capacidad="' + c + '" aria-pressed="' +
        (estado.capacidad === c) + '">' + U.esc(caps[c]) + '</button>';
    });
    h += '</div>';

    var lista = D.buscarFichas(estado.texto, estado.capacidad);
    if (!lista.length) {
      return h + '<p class="silencio">No hay ningún ejercicio que encaje. ' +
        'Si no está en las fuentes, no está aquí.</p>';
    }
    h += '<div class="lista">' + lista.map(function (f) {
      var niveles = f.niveles.map(function (n) { return n.nivel; }).join(', ');
      return '<a class="enlace-tarjeta" href="#/ejercicio/' + U.esc(f.id) + '">' +
        '<div class="enlace-tarjeta__titulo">' + U.esc(f.nombre) + '</div>' +
        '<div class="enlace-tarjeta__pie">' + U.esc(caps[f.capacidad] || f.capacidad) +
        (niveles ? ' · ' + U.esc(niveles) : '') + ' · ' + U.esc(f.clave || '') + '</div></a>';
    }).join('') + '</div>';
    return h;
  };

  V.ficha = function (id) {
    var f = D.ficha(id);
    if (!f) return '<h1>No existe esa ficha</h1><p><a href="#/ejercicios">Ver el catálogo</a></p>';
    var h = '<p class="pequeno no-imprimir"><a href="#/ejercicios">← Ejercicios</a></p>' +
      '<h1>' + U.esc(f.nombre) + '</h1>' +
      '<div class="etis">' + eti(D.ejercicios.capacidades[f.capacidad] || f.capacidad) +
      f.niveles.map(function (n) {
        return eti(n.nivel + ' · ' + n.patron, 'eti--gris');
      }).join('') + '</div>';

    h += '<div class="tarjeta"><h3>Cómo se hace</h3><p>' + U.esc(f.como) + '</p>';
    if (f.contenido) {
      h += '<ul>' + f.contenido.map(function (c) {
        return '<li>' + U.esc(c) + '</li>';
      }).join('') + '</ul>';
    }
    if (f.clave) h += '<h3>Clave</h3><p>' + U.esc(f.clave) + '</p>';
    if (f.error) {
      h += '<h3>Error frecuente</h3><p class="silencio">' + U.esc(f.error) + '</p>';
    }
    h += '</div>';

    var progresion = D.ejercicios.progresiones.filter(function (p) {
      return f.niveles.some(function (n) { return n.patron === p.patron; });
    });
    if (progresion.length) {
      h += '<h2>Su progresión</h2><div class="desliza"><table class="tabla">' +
        '<thead><tr><th>Nivel</th><th>Ejercicio</th></tr></thead><tbody>' +
        progresion.map(function (p) {
          var esta = p.ficha === f.id;
          return '<tr><td>' + U.esc(p.nivel) + '</td><td>' +
            (esta ? '<strong>' + U.esc(p.ejercicio) + '</strong>' :
              (p.ficha ? '<a href="#/ejercicio/' + U.esc(p.ficha) + '">' + U.esc(p.ejercicio) + '</a>'
                : U.esc(p.ejercicio))) + '</td></tr>';
        }).join('') + '</tbody></table></div>' +
        '<p class="pequeno silencio">No se sube de nivel hasta que el jugador ejecuta el ' +
        'actual con técnica limpia en todas las repeticiones de todas las series.</p>';
    }

    var usos = D.usosDeFicha(f.id);
    if (usos.length) {
      h += '<h2>Dónde aparece</h2><p class="sub">En ' + usos.length +
        ' de las 105 sesiones de la temporada.</p><div class="lista">' +
        usos.slice(0, 12).map(function (u) {
          return '<a class="enlace-tarjeta" href="#/sesion/' + u.sesion.fecha + '">' +
            '<div class="enlace-tarjeta__titulo">' + U.esc(u.dosis.join(' · ')) + '</div>' +
            '<div class="enlace-tarjeta__pie">' + U.esc(nombreSemana(u.semana)) + ' · ' +
            U.esc(U.fechaLarga(u.sesion.fecha)) + '</div></a>';
        }).join('') + '</div>';
      if (usos.length > 12) {
        h += '<p class="pequeno silencio">Y en ' + (usos.length - 12) + ' sesiones más.</p>';
      }
    }
    h += '<p class="pequeno silencio">Fuente: ' + U.esc(f.origen) + '</p>';
    return h;
  };

  V.rutina = function (id) {
    var r = D.rutina(id);
    if (!r) return '<h1>No existe esa rutina</h1>';
    var h = '<h1>' + U.esc(r.titulo) + '</h1>';
    h += r.notas.map(function (n) { return '<p class="sub">' + U.negritas(n) + '</p>'; }).join('');
    r.bloques.forEach(function (b) {
      if (b.nombre) h += '<h2>' + U.esc(b.nombre) + '</h2>';
      h += '<div class="desliza"><table class="tabla"><thead><tr><th>Ejercicio</th>' +
        '<th>Dosis</th><th>Tiempo</th></tr></thead><tbody>' +
        b.ejercicios.map(function (e) {
          return '<tr><td>' + U.esc(e.ejercicio) + '</td><td>' + U.esc(e.dosis) +
            '</td><td>' + U.esc(e.tiempo || '') + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    });
    h += '<p class="pequeno silencio">Fuente: ' + U.esc(r.origen) + '</p>';
    return h;
  };

  /* -------------------------------------------------------------- protocolos */

  V.protocolos = function () {
    var p = D.protocolos;
    var h = '<h1>Protocolos</h1>';

    h += '<div class="caja caja--alarma"><h2>Banderas rojas · derivación inmediata</h2>' +
      '<p>No pasan por progresión. Van al médico antes de la siguiente sesión.</p>' +
      '<div class="desliza"><table class="tabla"><thead><tr><th>Señal</th><th>Por qué</th></tr></thead><tbody>' +
      p.banderas_rojas.map(function (b) {
        return '<tr><td>' + U.negritas(b.senal) + '</td><td>' + U.negritas(b.porque) + '</td></tr>';
      }).join('') + '</tbody></table></div></div>';

    h += '<div class="caja caja--aviso"><h2>Qué es y qué no es esto</h2>' +
      p.aviso.map(function (t) { return '<p>' + U.negritas(t) + '</p>'; }).join('') + '</div>';

    h += '<h2>Protocolo de dolor</h2><p class="sub">Pregunta semanal, escala 0-10, ' +
      'rodilla, talón y espalda.</p><div class="desliza"><table class="tabla">' +
      '<thead><tr><th>Dolor</th><th>Qué hacer</th></tr></thead><tbody>' +
      D.temporada.protocolo_dolor.map(function (t) {
        return '<tr><td><strong>' + t.min + '-' + t.max + '</strong></td><td>' +
          U.esc(t.accion) + '</td></tr>';
      }).join('') + '</tbody></table></div>';

    h += '<h2>Semáforo semanal</h2><div class="desliza"><table class="tabla">' +
      '<thead><tr><th>Estado</th><th>Qué puede hacer</th></tr></thead><tbody>' +
      p.semaforo.map(function (s) {
        return '<tr><td>' + U.negritas(s.estado) + '</td><td>' + U.esc(s.puede) + '</td></tr>';
      }).join('') + '</tbody></table></div>';

    h += '<h2>Los cinco principios</h2>' +
      p.principios.map(function (t) { return '<p>' + U.negritas(t) + '</p>'; }).join('');

    h += '<h2>Batería de tests de vuelta a competir</h2><div class="desliza">' +
      '<table class="tabla"><thead><tr><th>Test</th><th>Cómo</th><th>Criterio</th></tr></thead><tbody>' +
      p.tests.map(function (t) {
        return '<tr><td>' + U.esc(t.test) + '</td><td>' + U.esc(t.como) + '</td><td>' +
          U.esc(t.criterio) + '</td></tr>';
      }).join('') + '</tbody></table></div>';

    h += '<h2>Protocolos por lesión</h2><div class="lista">' +
      p.lesiones.map(function (l) {
        return '<a class="enlace-tarjeta" href="#/lesion/' + U.esc(l.id) + '">' +
          '<div class="enlace-tarjeta__titulo">' + l.numero + ' · ' + U.esc(l.nombre) + '</div>' +
          '<div class="enlace-tarjeta__pie">' +
          (l.fases.length ? l.fases.length + ' fases con su criterio de paso' : 'Gestión de carga') +
          '</div></a>';
      }).join('') + '</div>';

    h += '<h2>Reintegración a pista</h2><div class="desliza"><table class="tabla">' +
      '<thead><tr><th>Paso</th><th>Qué hace</th><th>Duración</th></tr></thead><tbody>' +
      p.reintegracion.map(function (r) {
        return '<tr><td>' + U.negritas(r.paso) + '</td><td>' + U.negritas(r.que_hace) +
          '</td><td>' + U.esc(r.duracion) + '</td></tr>';
      }).join('') + '</tbody></table></div>' +
      '<p>' + U.negritas(p.reintegracion_nota) + '</p>';

    h += '<h2>Después del alta</h2>' +
      p.despues_del_alta.map(function (t) { return '<p>' + U.negritas(t) + '</p>'; }).join('');

    h += '<p class="pequeno silencio">Fuente: ' + U.esc(p.origen) + '</p>';
    return h;
  };

  V.lesion = function (id) {
    var l = D.protocolos.lesiones.filter(function (x) { return x.id === id; })[0];
    if (!l) return '<h1>No existe ese protocolo</h1>';
    var h = '<p class="pequeno no-imprimir"><a href="#/protocolos">← Protocolos</a></p>' +
      '<h1>' + U.esc(l.nombre) + '</h1>';
    if (l.fases.length) {
      h += '<div class="desliza"><table class="tabla"><thead><tr><th>Fase</th>' +
        '<th>Contenido</th><th>Criterio para pasar</th></tr></thead><tbody>' +
        l.fases.map(function (f) {
          return '<tr><td>' + U.negritas(f.fase) + '</td><td>' + U.negritas(f.contenido) +
            '</td><td>' + U.negritas(f.criterio) + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    }
    l.tablas.forEach(function (tb) {
      h += '<div class="desliza"><table class="tabla"><tbody>' + tb.map(function (fila) {
        return '<tr>' + fila.map(function (c) {
          return '<td>' + U.negritas(c) + '</td>';
        }).join('') + '</tr>';
      }).join('') + '</tbody></table></div>';
    });
    h += l.notas.map(function (t) { return '<p>' + U.negritas(t) + '</p>'; }).join('');
    h += '<p class="pequeno silencio">Fuente: ' + U.esc(D.protocolos.origen) + '</p>';
    return h;
  };

  /* --------------------------------------------------------- para jugadores */

  V.jugadores = function () {
    var j = D.jugadores;
    var h = '<h1>Para jugadores</h1>' +
      '<p class="sub">Dos cosas que se hacen en casa, sin entrenador delante.</p>';

    h += '<h2>' + U.esc(j.domingo.titulo) + '</h2>';
    h += j.domingo.notas.map(function (n) {
      return '<p class="pequeno silencio">' + U.negritas(n) + '</p>';
    }).join('');
    j.domingo.bloques.forEach(function (b) {
      h += '<div class="desliza"><table class="tabla"><thead><tr><th>Bloque</th>' +
        '<th>Ejercicio</th><th>Dosis</th></tr></thead><tbody>' +
        b.ejercicios.map(function (e) {
          return '<tr><td>' + U.negritas(e.grupo || '') + '</td><td>' + U.esc(e.ejercicio) +
            '</td><td>' + U.esc(e.dosis) + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    });

    h += '<h2>' + U.esc(j.navidad.titulo) + '</h2>';
    h += j.navidad.intro.map(function (t) { return '<p>' + U.negritas(t) + '</p>'; }).join('');
    j.navidad.sesiones.forEach(function (s) {
      h += '<h3>' + U.esc(s.titulo) + '</h3><div class="desliza"><table class="tabla">' +
        '<thead><tr><th>Ejercicio</th><th>Series × rep</th></tr></thead><tbody>' +
        s.ejercicios.map(function (e) {
          return '<tr><td>' + U.esc(e.ejercicio) + '</td><td>' + U.esc(e.dosis) + '</td></tr>';
        }).join('') + '</tbody></table></div>';
    });
    h += '<h3>Carrera</h3>' + j.navidad.carrera.map(function (t) {
      return '<p>' + U.negritas(t) + '</p>';
    }).join('');
    h += '<h3>Tu calendario</h3><div class="desliza"><table class="tabla"><tbody>' +
      j.navidad.calendario.map(function (c) {
        return '<tr><td>' + U.negritas(c.semana) + '</td><td>' + U.negritas(c.que) + '</td></tr>';
      }).join('') + '</tbody></table></div>';
    h += j.navidad.cierre.map(function (t) {
      return '<div class="caja caja--aviso"><p>' + U.negritas(t) + '</p></div>';
    }).join('');
    h += '<p class="no-imprimir"><button class="btn" data-accion="imprimir">Imprimir esta hoja</button></p>';
    return h;
  };

  window.V = V;
}());
