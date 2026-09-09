# Pruebas

Abren la web en un Chromium de verdad y comprueban lo que tiene que cumplirse
siempre. Necesitan el sitio servido:

```bash
python3 -m http.server 8777     # desde la raíz, en otra terminal
node pruebas/ejecutar.js        # todas
node pruebas/ejecutar.js hoy    # solo las que contengan «hoy»
```

Sale 0 si pasan todas, 1 si falla alguna y 2 si no encuentra el servidor. Para
comprobar lo ya publicado, sírvelo en otro puerto y usa `BASE`:

```bash
BASE=https://aitor1393.github.io/PreparacionFisicaBasket/ node pruebas/ejecutar.js
```

**Playwright vive en `pruebas/package.json`, no en la raíz**, a propósito: la
web no tiene dependencias y se abre sin instalar nada.

## Qué cubre cada una

| Prueba | Qué protege |
|---|---|
| carga sin errores | Que no haya excepciones de JavaScript en la pantalla de entrada |
| hoy enseña la fecha de hoy | Que la pantalla de entrada localice el día, y que fuera de temporada caiga al calendario |
| el calendario lista las 39 semanas | Que no se pierda ninguna semana entre el JSON y la pantalla |
| cada semana presencial enseña sus tres sesiones | Lunes, miércoles y viernes, en las semanas de las tres puntas del calendario |
| las semanas autónomas no fingen tener sesión | Que el parón se vea como parón y no como una semana vacía |
| los bloques suman los minutos | Que la hora cuadre: 55 el lunes, 50 el miércoles y el viernes |
| una sesión por plantilla dice cuántas series | El dato que el entrenador necesita en diez segundos |
| los ejercicios enlazan con su ficha | Que tocar un ejercicio lleve a su ficha y no a otra |
| el catálogo filtra | Buscador y filtros por capacidad |
| la sesión dice el descanso entre series | Que se vea la referencia del catálogo, que es la mitad de lo que dura el bloque |
| todo bloque de movilidad lleva a sus ejercicios | Con rutina exacta o sin ella, que siempre haya salida al listado |
| la ficha enseña los seis campos | Montaje, ejecución, instrucción de banda destacada y arriba, error con corrección, regresión y progresión, material visual |
| un término de búsqueda no se convierte en enlace | Que un 🔍 abra una búsqueda y no un enlace directo inventado |
| los protocolos ponen las banderas rojas primero | Lo que pide el brief, y que no se diluya qué es competencia médica |
| la ruta de jugadores no arrastra jerga | Que no se cuele «microciclo» ni «pliometría» en la hoja del jugador |
| funciona sin conexión | El service worker, que es lo que la salva en un pabellón sin cobertura |
| la impresión oculta la navegación | Que una sesión salga en una hoja limpia |
| cabe en 360 px | Que ninguna pantalla se desborde a lo ancho en un móvil |

## Al escribir una nueva

Dos reglas que ya han provocado rojos falsos en proyectos parecidos:

- **No fijes cifras que dependan del contenido.** «Espera 105 sesiones» caduca
  en cuanto se toque un documento. Comprueba propiedades y saca los números del
  propio JSON, como hacen las de arriba.
- **Espera a que la vista esté pintada.** Las vistas se repintan enteras al
  cambiar de ruta, así que el `h1` viejo sigue en el DOM un instante. Espera al
  hash y a algo propio de la pantalla nueva, no a un selector genérico.
