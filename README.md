# Preparación física · Cadete Masculino 2026/2027

La planificación física de una temporada de baloncesto cadete, consultable
desde el móvil. Sitio **estático**: HTML, CSS y JavaScript a pelo, sin
dependencias y sin compilación. Se sirve y funciona.

El problema que resuelve lo dice el [brief](BRIEF-web.md): la planificación
existe en un Word de 58 páginas, y el entrenador la consulta en el pabellón,
desde el teléfono, con cinco minutos antes de empezar. Un documento de 58
páginas no sirve para eso.

## Qué hace

**Hoy.** La pantalla de entrada. Localiza la fecha en el calendario y enseña la
sesión que toca con sus bloques, sus minutos y sus ejercicios. Si es sábado,
el partido; si es domingo, la rutina de regeneración; si es una semana de
parón, el plan autónomo; y fuera de temporada cae al calendario.

Se entrena **martes, miércoles y viernes**, 50 minutos cada día. Martes y
miércoles son consecutivos: el martes lleva el trabajo neural, que exige
frescura, y el miércoles la fuerza, que tolera fatiga previa.

**Calendario.** Las 39 semanas con su carga, su mesociclo y su jornada, con la
lógica del póster: barra de carga, color por tipo de bloque y las semanas sin
partido a la vista. Cada semana lleva a su detalle.

**Microciclo y sesión.** Las tres sesiones de la semana y el detalle de cada
una. Cada ejercicio enlaza con su ficha y cada bloque de movilidad con su
rutina cronometrada. Cualquier sesión se imprime en una hoja limpia.

**Ejercicios.** 85 fichas buscables y filtrables por capacidad, con los seis
campos que pide el brief: montaje, ejecución, **instrucción en voz alta**,
error frecuente con su corrección, regresión y progresión, y material visual.

La instrucción de banda va la primera y destacada: es lo que se lee en tres
segundos con el ejercicio ya empezado. Del material visual, **▶** es un enlace
comprobado y **🔍** un término de búsqueda que abre el buscador con esa frase
exacta. Un 🔍 nunca se convierte en un enlace directo inventado.

**Ninguna ficha se queda sin nada a lo que tirar.** Las que el apéndice todavía
no cubre reciben una búsqueda construida con su nombre, marcada en pantalla
como automática: no es lo mismo que un enlace comprobado y el entrenador tiene
que poder distinguirlo. Cuáles son está en
[`informes/sin-material-visual.md`](informes/sin-material-visual.md), que se
regenera solo; añadir un ▶ o un 🔍 en el apéndice sustituye la búsqueda.

**Protocolos.** Las banderas rojas primero y bien visibles, después el
protocolo de dolor, el semáforo semanal, la batería de tests y los cinco
protocolos por lesión.

**Para jugadores.** Ruta aparte y sin jerga, para compartir por enlace: la
rutina del domingo y el plan de Navidad.

Funciona **sin conexión** una vez cargada, que es lo que hace falta en un
pabellón con mala cobertura.

## Cómo está hecho

```
index.html                  una sola página; las vistas se pintan por JS
assets/css/estilos.css      móvil primero, claro y oscuro, hoja de impresión
assets/js/                  ver el orden de carga más abajo
sw.js                       service worker: caché primero, refresco por detrás
datos-temporada.json        el calendario. Escrito a mano, fuente de verdad
fuentes/*.md                el contenido deportivo. Única verdad
data/*.json                 GENERADO. No editar a mano
informes/                   GENERADO. Qué le falta al contenido
scripts/generar.py          lo que convierte fuentes/ en data/
pruebas/ejecutar.js         14 pruebas en un Chromium de verdad
entregables/                Word, póster, hoja del domingo y Excel de seguimiento
```

### El orden de carga importa

No hay imports: cada archivo cuelga su objeto de `window` y los siguientes lo
usan.

| Archivo | Global | Qué hace |
|---|---|---|
| `util.js` | `U` | fechas, formato, DOM, `localStorage`. Sin dependencias |
| `datos.js` | `D` | el modelo: carga los JSON y contesta qué toca hoy. **Aquí van las reglas** |
| `vistas.js` | `V` | genera HTML. No decide nada |
| `app.js` | `App` | rutas, delegación de eventos, arranque |

Si te ves calculando algo dentro de un `V.`, casi seguro va en `D.`.

## El contenido no se copia: se genera

El brief lo pide y es la decisión que sostiene todo lo demás: **nada del
contenido deportivo se escribe a mano dos veces.** Los nueve markdown de
`fuentes/` y `datos-temporada.json` son la única verdad, y `scripts/generar.py`
los convierte en los cuatro JSON que consume la web.

```bash
python3 scripts/generar.py
```

Cada sesión guarda **el texto original de su fuente** además de los campos
partidos, y lleva anotado de qué archivo y de qué sección sale. Si algún día el
troceado se equivoca, el entrenador sigue leyendo lo que dice el documento.

El generador **sale en rojo** si una fuente no tiene la forma esperada o si
falla una comprobación estructural: que las 35 semanas presenciales tengan sus
tres días, que ninguna sesión se quede sin bloques, y que cada semana lleve
sus contenidos fijos. Más vale que falle a que publique una sesión a medias.

Aparte, imprime **avisos de fuente**: los casos en que dos documentos se
contradicen entre sí —un encabezado con una fecha que el calendario desmiente,
unos bloques que no suman la duración de su sesión, una etiqueta de tipo que
no cuadra con el día—. Eso no tumba la generación porque **se arregla en el
documento, no en el código**, pero queda a la vista en cada ejecución.

Las tres formas de sesión no significan lo mismo y la web las distingue:

| | |
|---|---|
| **explícita** | el documento detalla ese día concreto |
| **por plantilla** | el documento asigna una plantilla (N1, F2, C…) y la carga de la semana decide las series |
| **autónoma** | no hay sesión presencial: manda el plan del jugador |

## Probar los cambios

```bash
python3 -m http.server 8777     # desde la raíz, en otra terminal
node pruebas/ejecutar.js
```

Detalles y qué cubre cada una en [`pruebas/README.md`](pruebas/README.md).
Playwright vive en `pruebas/package.json`, no en la raíz, para que la web siga
sin dependencias.

## La Action

`pages.yml` valida y despliega en cada push a `main`. Además de pasar las
pruebas, **regenera `data/` y falla si no coincide con `fuentes/`**: es lo que
evita que alguien edite un documento, se olvide de generar y la web siga
sirviendo la versión vieja sin que nadie se entere.

**Se publica solo la web**, no el repositorio entero:

```
index.html · sw.js · assets/ · data/
```

Fuera se quedan `fuentes/`, `entregables/`, `scripts/` y `pruebas/`. No hacen
falta para que la web funcione y no tienen por qué ser descargables desde la
dirección que se le pasa al equipo.

Ojo con la distinción: eso los quita del **sitio publicado**, pero siguen en el
repositorio, que es público. Si algún día tienen que dejar de estar al alcance
de cualquiera, hay que sacarlos del repositorio, no del despliegue.

## Límites

- El contenido deportivo **no se inventa ni se modifica**. Si no está en las
  fuentes, no está en la web.
- Los protocolos de lesión describen progresión de carga a partir de un
  diagnóstico y una autorización médica. La web conserva esa distinción tal
  como la escribe el documento y no la diluye.
- Fase 2 del brief —registro de RPE y dolor por parte de los jugadores— **no
  está construida y no se empieza sin hablarlo**: implica datos personales de
  menores.
