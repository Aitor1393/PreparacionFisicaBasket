/* Pruebas de la web en un Chromium de verdad.

   Uso, con el sitio servido en el puerto 8777:
     python3 -m http.server 8777
     node pruebas/ejecutar.js
     node pruebas/ejecutar.js hoy        (solo las que contengan «hoy»)

   Sale 0 si pasan todas, 1 si falla alguna y 2 si no encuentra el servidor.

   Regla al escribir una nueva: no fijes cifras que dependan del contenido
   («espera 105 sesiones» caduca en cuanto se toque un documento). Comprueba
   propiedades y saca los números del propio JSON. */

const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

const BASE = process.env.BASE || 'http://localhost:8777/';
const filtro = process.argv[2] || '';
const raiz = path.join(__dirname, '..');
const semanas = JSON.parse(fs.readFileSync(path.join(raiz, 'data/semanas.json'), 'utf8'));
const ejercicios = JSON.parse(fs.readFileSync(path.join(raiz, 'data/ejercicios.json'), 'utf8'));

const pruebas = [];
const prueba = (nombre, fn) => pruebas.push({ nombre, fn });

function afirmar(condicion, mensaje) {
  if (!condicion) throw new Error(mensaje);
}

/* Va a una ruta y espera a que la pantalla esté pintada. Sin esto las pruebas
   se leen el «Cargando la temporada…» y fallan por carreras, no por errores. */
async function ir(page, hash) {
  await page.goto(BASE + '#' + hash, { waitUntil: 'domcontentloaded' });
  await page.evaluate(() => window.location.reload());
  await page.waitForFunction(() => window.D && window.D.cargado, null, { timeout: 15000 });
  await page.waitForFunction(() => !document.querySelector('#app .cargando'), null, { timeout: 15000 });
}

/* ------------------------------------------------------------------ pruebas */

prueba('carga sin errores de consola ni de página', async (page, errores) => {
  await ir(page, '/hoy');
  afirmar(errores.length === 0, 'errores en consola: ' + errores.join(' | '));
});

prueba('hoy enseña la fecha de hoy y su semana', async (page) => {
  await ir(page, '/hoy');
  const texto = await page.textContent('#app');
  const hoy = new Date();
  const meses = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio',
                 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const dentro = semanas.semanas.some(s => {
    // El calendario ya no guarda el lunes: se entrena martes, miércoles y
    // viernes. La semana sigue yendo de lunes a domingo.
    const lunes = new Date(s.martes + 'T12:00:00'); lunes.setDate(lunes.getDate() - 1);
    const domingo = new Date(lunes); domingo.setDate(domingo.getDate() + 6);
    return hoy >= lunes && hoy <= domingo;
  });
  if (dentro) {
    afirmar(texto.includes(meses[hoy.getMonth()]), 'no aparece el mes en curso');
  } else {
    // Fuera de temporada el brief pide caer al calendario. Se comprueba la
    // propiedad, no el titular: el texto puede cambiar y la prueba no debe.
    const filas = await page.locator('.cal__fila').count();
    afirmar(filas === semanas.semanas.length,
      'estamos fuera de temporada y no cae al calendario');
    afirmar(/temporada/i.test(texto), 'no dice nada de la temporada');
  }
});

prueba('el calendario lista las 39 semanas del JSON', async (page) => {
  await ir(page, '/calendario');
  const filas = await page.locator('.cal__fila').count();
  afirmar(filas === semanas.semanas.length,
    `hay ${filas} filas y el JSON trae ${semanas.semanas.length} semanas`);
});

prueba('cada semana presencial enseña sus tres sesiones', async (page) => {
  const presenciales = semanas.semanas.filter(s => s.formato === 'presencial');
  for (const s of [presenciales[0], presenciales[Math.floor(presenciales.length / 2)],
                   presenciales[presenciales.length - 1]]) {
    await ir(page, '/semana/' + s.semana);
    const tarjetas = await page.locator('.enlace-tarjeta').count();
    afirmar(tarjetas >= s.sesiones.length,
      `semana ${s.semana}: ${tarjetas} tarjetas para ${s.sesiones.length} sesiones`);
  }
});

prueba('las semanas autónomas no fingen tener sesión', async (page) => {
  const autonomas = semanas.semanas.filter(s => s.formato === 'autonomo');
  afirmar(autonomas.length > 0, 'el JSON no trae ninguna semana autónoma');
  for (const s of autonomas) {
    await ir(page, '/semana/' + s.semana);
    const texto = await page.textContent('#app');
    afirmar(/sin sesión presencial/i.test(texto),
      `semana ${s.semana}: no avisa de que no hay sesión presencial`);
  }
});

prueba('los bloques de una sesión suman los minutos de la sesión', async (page) => {
  const conMinutos = [];
  semanas.semanas.forEach(s => s.sesiones.forEach(ses => {
    if (ses.bloques.every(b => b.min !== null)) conMinutos.push(ses);
  }));
  afirmar(conMinutos.length > 0, 'ninguna sesión tiene todos los bloques con minutos');
  for (const ses of conMinutos.slice(0, 3)) {
    await ir(page, '/sesion/' + ses.fecha);
    const minutos = await page.locator('.bloque__min').allTextContents();
    const suma = minutos.reduce((n, t) => n + (parseInt(t, 10) || 0), 0);
    afirmar(suma === ses.minutos,
      `${ses.fecha}: los bloques pintados suman ${suma} y la sesión dura ${ses.minutos}`);
  }
});

prueba('una sesión por plantilla dice cuántas series toca esa semana', async (page) => {
  const s = semanas.semanas.find(x => x.sesiones.some(y => y.estado === 'plantilla'));
  afirmar(s, 'no hay ninguna semana que se resuelva por plantilla');
  const ses = s.sesiones.find(y => y.estado === 'plantilla');
  await ir(page, '/sesion/' + ses.fecha);
  const texto = await page.textContent('#app');
  const series = semanas.series_por_carga[String(s.carga)];
  afirmar(texto.includes(series), `no aparece «${series}» en la sesión del ${ses.fecha}`);
});

prueba('los ejercicios de una sesión enlazan con su ficha', async (page) => {
  let objetivo = null;
  semanas.semanas.forEach(s => s.sesiones.forEach(ses => {
    if (!objetivo && ses.bloques.some(b => (b.ejercicios || []).some(e => e.ficha))) objetivo = ses;
  }));
  afirmar(objetivo, 'ninguna sesión tiene ejercicios enlazados');
  await ir(page, '/sesion/' + objetivo.fecha);
  const enlace = page.locator('.ejercicios a').first();
  const nombre = (await enlace.textContent()).trim();
  const destino = (await enlace.getAttribute('href')).slice(1);
  await enlace.click();
  // Hay que esperar a que la ruta cambie y a que la vista se repinte: el h1
  // de la sesión sigue en el DOM hasta que App.pintar sustituye #app.
  await page.waitForFunction((d) => location.hash === '#' + d, destino, { timeout: 5000 });
  await page.waitForFunction(
    (d) => !!document.querySelector('#app h1') &&
           !!document.querySelector('#app .pequeno a[href="#/ejercicios"]'), destino,
    { timeout: 5000 });
  const titulo = await page.textContent('#app h1');
  afirmar(nombre.toLowerCase().startsWith(titulo.toLowerCase().slice(0, 8)),
    `«${nombre}» ha abierto la ficha «${titulo}»`);
});

prueba('el catálogo filtra por capacidad y por texto', async (page) => {
  await ir(page, '/ejercicios');
  const todas = await page.locator('.lista .enlace-tarjeta').count();
  afirmar(todas === ejercicios.fichas.length,
    `salen ${todas} fichas y el JSON trae ${ejercicios.fichas.length}`);

  const capacidad = Object.keys(ejercicios.capacidades)[0];
  const esperadas = ejercicios.fichas.filter(f => f.capacidad === capacidad).length;
  await page.click(`.filtro[data-capacidad="${capacidad}"]`);
  await page.waitForFunction(
    (n) => document.querySelectorAll('.lista .enlace-tarjeta').length === n, esperadas);
  const filtradas = await page.locator('.lista .enlace-tarjeta').count();
  afirmar(filtradas === esperadas && filtradas < todas,
    `el filtro «${capacidad}» deja ${filtradas} y deberían ser ${esperadas}`);
});

prueba('la ficha enseña los seis campos y destaca la instrucción de banda', async (page) => {
  // Se elige una ficha que tenga los seis, para comprobar que se pintan todos.
  const completa = ejercicios.fichas.find(f =>
    f.montaje && f.ejecucion && f.voz_alta && f.error && (f.regresion || f.progresion) &&
    f.video && f.video.length);
  afirmar(completa, 'ninguna ficha del JSON trae los seis campos');
  await ir(page, '/ejercicio/' + completa.id);
  const texto = await page.textContent('#app');
  for (const [nombre, valor] of [['montaje', completa.montaje], ['ejecución', completa.ejecucion],
                                 ['error frecuente', completa.error]]) {
    afirmar(texto.includes(valor.slice(0, 40)), `no se ve el campo ${nombre}`);
  }
  // La instrucción verbal va destacada y aparte, no perdida entre el resto.
  const voz = await page.locator('.voz__texto').textContent();
  afirmar(voz.trim() === completa.voz_alta.trim(),
    'la instrucción en voz alta no está en su bloque destacado');
  const antes = texto.indexOf(completa.voz_alta.slice(0, 20));
  afirmar(antes >= 0 && antes < texto.indexOf(completa.ejecucion.slice(0, 20)),
    'la instrucción en voz alta no sale antes que la ejecución');
});

prueba('un término de búsqueda no se convierte en un enlace inventado', async (page) => {
  const conBusqueda = ejercicios.fichas.find(f =>
    (f.video || []).some(v => v.tipo === 'busqueda'));
  afirmar(conBusqueda, 'ninguna ficha trae un término de búsqueda');
  const termino = conBusqueda.video.find(v => v.tipo === 'busqueda').termino;
  await ir(page, '/ejercicio/' + conBusqueda.id);
  const enlaces = await page.locator('.medios a').evaluateAll(
    as => as.map(a => a.getAttribute('href')));
  const dela = enlaces.filter(h => h.includes(encodeURIComponent(termino).slice(0, 20)));
  afirmar(dela.length === 1, 'el término de búsqueda no aparece una sola vez');
  afirmar(/\/results\?search_query=/.test(dela[0]),
    'el término abre un enlace directo en vez de una búsqueda: ' + dela[0]);
});

prueba('toda ficha tiene a dónde tirar para ver el ejercicio', async (page) => {
  const sinNada = ejercicios.fichas.filter(f => !f.video || !f.video.length);
  afirmar(sinNada.length === 0,
    'fichas sin material visual: ' + sinNada.map(f => f.nombre).join(', '));

  // Y una búsqueda automática tiene que decir que lo es: no es lo mismo que un
  // enlace comprobado y el entrenador tiene que poder distinguirlo.
  const automatica = ejercicios.fichas.find(f =>
    (f.video || []).some(v => v.automatica));
  if (automatica) {
    await ir(page, '/ejercicio/' + automatica.id);
    const texto = await page.textContent('.medios');
    afirmar(/autom[áa]tica/i.test(texto),
      'una búsqueda automática se enseña como si fuera material comprobado');
  }
});

prueba('la sesión dice el descanso entre series', async (page) => {
  // El descanso no lo escribe ninguna sesión: sale de la tabla del catálogo.
  // Sin él, media hora de fuerza parece mucho para cinco ejercicios.
  let objetivo = null;
  semanas.semanas.forEach(s => s.sesiones.forEach(ses => {
    if (!objetivo && ses.bloques.some(b => (b.descansos || []).length)) objetivo = ses;
  }));
  afirmar(objetivo, 'ninguna sesión trae descansos');
  await ir(page, '/sesion/' + objetivo.fecha);
  const texto = await page.textContent('#app');
  const esperado = objetivo.bloques.find(b => (b.descansos || []).length).descansos[0];
  afirmar(texto.includes(esperado.descanso),
    `no se ve el descanso «${esperado.descanso}» de ${objetivo.fecha}`);
});

prueba('todo bloque de movilidad lleva a sus ejercicios', async (page) => {
  const conMovilidad = [];
  semanas.semanas.forEach(s => s.sesiones.forEach(ses => {
    if (ses.bloques.some(b => b.es_movilidad)) conMovilidad.push(ses);
  }));
  afirmar(conMovilidad.length > 0, 'ninguna sesión tiene bloque de movilidad');
  // Se prueban una con rutina exacta y otra sin ella: las dos tienen que
  // ofrecer salida, que era justo lo que faltaba.
  const conRutina = conMovilidad.find(s => s.bloques.some(b => b.es_movilidad && b.rutina));
  const sinRutina = conMovilidad.find(s => s.bloques.some(b => b.es_movilidad && !b.rutina));
  for (const ses of [conRutina, sinRutina].filter(Boolean)) {
    await ir(page, '/sesion/' + ses.fecha);
    const enlaces = await page.locator('.remite a').evaluateAll(
      as => as.map(a => a.getAttribute('href')));
    afirmar(enlaces.some(h => /^#\/rutinas?/.test(h)),
      `${ses.fecha}: el bloque de movilidad no lleva a ninguna rutina`);
  }
});

prueba('los protocolos ponen las banderas rojas antes que nada', async (page) => {
  await ir(page, '/protocolos');
  const texto = await page.textContent('#app');
  const banderas = texto.indexOf('Banderas rojas');
  const dolor = texto.indexOf('Protocolo de dolor');
  afirmar(banderas >= 0 && dolor > banderas,
    'las banderas rojas no salen las primeras');
  afirmar(/no corresponde a este documento|Diagnosticar/i.test(texto),
    'no se conserva el aviso de qué no es competencia del preparador');
});

prueba('la ruta de jugadores no arrastra la jerga del resto', async (page) => {
  await ir(page, '/jugadores');
  const texto = await page.textContent('#app');
  afirmar(/rutina/i.test(texto) && /Plan de Navidad/i.test(texto),
    'faltan la rutina del domingo o el plan de Navidad');
  afirmar(!/microciclo|mesociclo|pliometr/i.test(texto),
    'se ha colado vocabulario de entrenador en la hoja del jugador');
});

prueba('funciona sin conexión una vez cargada', async (page, errores, contexto) => {
  await ir(page, '/hoy');
  await page.waitForFunction(() => navigator.serviceWorker.controller !== null,
    null, { timeout: 15000 });
  await contexto.setOffline(true);
  try {
    await page.reload({ waitUntil: 'domcontentloaded' });
    await page.waitForFunction(() => window.D && window.D.cargado, null, { timeout: 15000 });
    const texto = await page.textContent('#app');
    afirmar(!/no se han podido cargar/i.test(texto), 'sin red no carga los datos');
  } finally {
    await contexto.setOffline(false);
  }
});

prueba('la impresión oculta la navegación', async (page) => {
  await ir(page, '/calendario');
  await page.emulateMedia({ media: 'print' });
  const visible = await page.locator('.nav').isVisible();
  await page.emulateMedia({ media: 'screen' });
  afirmar(!visible, 'la barra de navegación se imprime');
});

prueba('cabe en una pantalla de móvil sin desplazamiento lateral', async (page) => {
  await page.setViewportSize({ width: 360, height: 740 });
  for (const r of ['/hoy', '/calendario', '/ejercicios', '/protocolos', '/jugadores']) {
    await ir(page, r);
    const desborda = await page.evaluate(() =>
      document.documentElement.scrollWidth > document.documentElement.clientWidth + 1);
    afirmar(!desborda, `${r} se desborda a lo ancho en 360 px`);
  }
  await page.setViewportSize({ width: 1280, height: 900 });
});

/* -------------------------------------------------------------------- lanzar */

(async () => {
  try {
    const r = await fetch(BASE);
    if (!r.ok) throw new Error('respuesta ' + r.status);
  } catch (e) {
    console.error('No hay servidor en ' + BASE + ' (' + e.message + ').');
    console.error('Levántalo con:  python3 -m http.server 8777');
    process.exit(2);
  }

  const navegador = await chromium.launch();
  let fallos = 0, saltadas = 0;

  for (const p of pruebas) {
    if (filtro && !p.nombre.includes(filtro)) { saltadas++; continue; }
    const contexto = await navegador.newContext();
    const page = await contexto.newPage();
    const errores = [];
    page.on('console', m => { if (m.type() === 'error') errores.push(m.text()); });
    page.on('pageerror', e => errores.push(e.message));
    try {
      await p.fn(page, errores, contexto);
      console.log('  ok  ' + p.nombre);
    } catch (e) {
      fallos++;
      console.log('FALLA  ' + p.nombre);
      console.log('       ' + e.message);
    }
    await contexto.close();
  }

  await navegador.close();
  const pasadas = pruebas.length - saltadas - fallos;
  console.log('\n' + pasadas + ' de ' + (pruebas.length - saltadas) + ' pruebas pasan' +
    (saltadas ? ' (' + saltadas + ' fuera del filtro)' : ''));
  process.exit(fallos ? 1 : 0);
})();
