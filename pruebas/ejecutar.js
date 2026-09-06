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
    const lunes = new Date(s.lunes + 'T12:00:00');
    const domingo = new Date(lunes); domingo.setDate(domingo.getDate() + 6);
    return hoy >= lunes && hoy <= domingo;
  });
  if (dentro) {
    afirmar(texto.includes(meses[hoy.getMonth()]), 'no aparece el mes en curso');
  } else {
    afirmar(texto.includes('Fuera de temporada'),
      'estamos fuera de temporada y no lo dice; cae al calendario');
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
