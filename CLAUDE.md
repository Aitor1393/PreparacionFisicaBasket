# CLAUDE.md

Contexto del proyecto para agentes que trabajen en este repositorio.

## Qué es esto

Planificación física completa de un equipo **cadete masculino de baloncesto** (14-15 años) para la temporada 2026/2027. El contenido deportivo ya está cerrado y validado. Encima de él hay una **web de consulta**, que es lo que se desarrolla en este repositorio.

**El contenido deportivo no se inventa ni se modifica.** Los documentos fuente son la única verdad. Si algo no está en ellos, no existe.

## Cómo está hecha la web

Sitio estático sin dependencias ni compilación. `README.md` lo explica entero; lo imprescindible antes de tocar nada:

- **El contenido no se copia, se genera.** `scripts/generar.py` convierte `/fuentes` y `datos-temporada.json` en los JSON de `data/`. **`data/` no se edita a mano nunca.** Después de tocar una fuente, hay que volver a generar; la Action falla si no coincide.
- El generador **sale en rojo** si una fuente cambia de forma o si falla una comprobación. Eso es lo que se espera de él: mejor rojo que publicar una sesión a medias.
- Cada sesión guarda el texto original de su fuente y de qué archivo y sección sale.
- Las reglas van en `assets/js/datos.js`; `vistas.js` solo pinta.
- Antes de dar algo por hecho, pasa las pruebas: `python3 -m http.server 8777` y `node pruebas/ejecutar.js`.
- Se publica solo la web: `scripts/preparar-sitio.sh` arma `_sitio/`. Los entregables y las fuentes no se sirven.

## Idioma

Todo en **español de España**. Interfaz, comentarios, nombres de variables de dominio, commits. Sin anglicismos innecesarios: se dice "fuerza", no "strength"; "microciclo", no "microcycle".

## Contexto deportivo mínimo

| Dato | Valor |
|---|---|
| Competición | FBM Preferente, 1ª o 2ª División, Serie "A" |
| Formato | 12 equipos, 22 jornadas a doble vuelta, play-off para los 6 primeros |
| Objetivo | Clasificar para play-off |
| Temporada | 7 sep 2026 – 6 jun 2027, **39 microciclos** |
| Entrenamientos | **Martes, miércoles y viernes**, 50 min cada sesión |
| Partido | Sábado |
| Domingo | Descanso, con rutina autónoma de 20 min |

**Restricciones que condicionan todo el diseño:**

- El trabajo físico va **siempre antes** del entrenamiento de pista. La hora no se puede partir.
- Duraciones: **50 minutos los tres días**.
- Material: **solo gomas elásticas, conos y escalera de agilidad**. No hay pesas, barras, balón medicinal, espalderas ni barra de dominadas. La carga progresa por palanca, unilateralidad, tempo, rango, tensión elástica, densidad e intención de velocidad.
- El viernes es víspera de partido: no admite carga.

## Vocabulario

- **Mesociclo**: bloque de la temporada. M0 a M9.
- **Microciclo**: una semana. Numeradas 1-39 en el calendario global; dentro de M1-M9 se nombran MC1-MC31.
- **Carga**: índice subjetivo de exigencia del microciclo, escala 1-10.
- **Contactos**: número de aterrizajes de pliometría programados en la semana.
- **Plantilla de sesión**: N1, N2 (martes, trabajo neural), F1, F2 (miércoles, fuerza), C (viernes víspera), D (viernes de carga).
- **Jornada**: partido de liga. J1 a J22, más segunda fase.
- **MD-n**: días hasta el partido. Martes = MD-4, miércoles = MD-3, viernes = MD-1.

**Martes y miércoles son días consecutivos.** Por eso el martes lleva todo el trabajo neural (pliometría, velocidad, cambios de dirección), que exige frescura, y el miércoles toda la fuerza, que tolera fatiga previa. Invertir ese orden degrada la calidad del salto y del sprint.

## Si vienes a actualizar una web ya construida

Lee **`CAMBIOS.md`** antes que nada. Recoge todo lo que ha cambiado respecto a la versión anterior, incluido un cambio estructural de días de entrenamiento que afecta a todas las pantallas.

## Archivos fuente

Contenido deportivo, en `/fuentes`:

| Archivo | Contiene |
|---|---|
| `catalogo-ejercicios-progresiones-cadete.md` | Catálogo por capacidad, con niveles N1-N5 y fases F1-F4 |
| `Apendice-movilidad-y-ejercicios.md` | Rutinas de movilidad cronometradas y **ficha completa de cada ejercicio**: montaje, ejecución, instrucción verbal, error frecuente con su corrección, regresión y progresión, y enlace a vídeo o término de búsqueda |
| `M0-pretemporada-sesiones-v2.md` | 12 sesiones de pretemporada |
| `M1-acumulacion-sesiones.md` | 24 sesiones, 8 microciclos |
| `M2-intensificacion-sesiones.md` | 9 sesiones, 3 microciclos |
| `M3-navidad-plan.md` | Plan autónomo de Navidad y semana de reactivación |
| `M4-M5-mantenimiento-sesiones.md` | 8 microciclos con plantillas rotatorias |
| `M6-M9-cierre-temporada.md` | De Semana Santa al play-off |
| `Protocolo-vuelta-tras-lesion.md` | Protocolos por lesión y banderas rojas |

Datos estructurados: `datos-temporada.json`. Es el calendario completo, las plantillas de sesión, el protocolo de dolor, los contenidos fijos, las bibliotecas de vídeo y los enlaces verificados por ejercicio. **Úsalo como fuente para todo lo que sea calendario o carga**, en lugar de parsear los markdown.

Nota: `M0-pretemporada-sesiones.md` (sin `-v2`) es una versión obsoleta con semana de evaluación. No usarla.

## Decisiones contrastadas · No cambiar sin evidencia

Estas se revisaron contra literatura externa y algunas corrigen lo que dice el material del curso de entrenador. Si un texto generado las contradice, es un error.

1. **Velocidad alta todos los martes**, **3 minutos de descanso**. La exposición regular al sprint protege el isquiotibial; espaciarla es peor. **La progresión no es plana**: sube en las ventanas de carga (de 5×20 m en MC1 a 6×30 m en MC6-MC7 y MC20) y se congela en 4-5×25 m durante el bloque denso de febrero.
8. **CMJ cada tres semanas**, tres saltos al empezar el martes, en las semanas 2, 5, 8, 11, 14, 20, 23, 26, 28, 31, 34 y 37. Es el único dato que dice si la explosividad mejora.
9. **Aceleración resistida con goma** en MC1, MC3, MC4, MC7, MC9 y MC20. Resistencia ligera: si cambia el patrón de carrera, sobra tensión.
2. **Curl nórdico todos los miércoles**, sin excepción.
3. **Sentadilla española**: se usa porque aporta carga tolerable en competición, **no** porque tenga efecto analgésico. Ese efecto está poco demostrado. No escribir que "quita el dolor".
4. **Umbral de crecimiento: 1,2 cm entre mediciones de dos meses** (equivale a 7,2 cm/año). No 2 cm.
5. **Estiramiento estático**: no previene lesiones. La rutina del domingo es movilidad, automasaje y respiración. No venderla como prevención.
6. **Trabajo intermitente 15"/15"**: en el viernes de las semanas sin partido (5, 8, 13, 28, 34) para todo el equipo, y después del partido del sábado para quien haya jugado menos de 15 minutos. Nunca antes de pista en semanas normales: degradaría la sesión de pista posterior.
7. **Protocolo de dolor**: 0-3 normal, 4-6 sin pliometría el martes, 7+ sin pliometría ni velocidad y valoración médica.

## Material visual

En el apéndice, **▶** marca enlaces verificados uno a uno y **🔍** marca un término de búsqueda porque no hay enlace estable. Al construir la web:

- Los enlaces ▶ se muestran como enlace externo, abriendo en pestaña nueva.
- Los 🔍 se muestran como botón de búsqueda que abre el buscador con ese término exacto. **No los conviertas en enlaces directos inventados.**
- Las cinco bibliotecas de referencia del JSON van en la ficha de ejercicio como fuentes alternativas.
- No incrustes vídeos de terceros sin comprobar que la licencia lo permite. Enlazar sí, incrustar es otra cosa.

## Límites

- **No dar consejo médico.** Los protocolos de lesión describen progresión de carga partiendo de que ya hay diagnóstico y autorización. La web debe mostrar esa distinción, no diluirla.
- **No inventar ejercicios, dosis ni fechas.** Todo sale de los fuentes.
- **No modificar el calendario.** Las fechas vienen de las bases oficiales de la FBM.
- No añadir funcionalidad de seguimiento de datos personales de menores sin plantearlo antes: hay implicaciones de protección de datos.

## Herramientas usadas para generar los entregables

Por si hay que regenerar alguno:

- Documento Word: `pandoc combined.md -o salida.docx --toc --toc-depth=2 --standalone`
- PDFs (póster de calendario, hoja del domingo): `reportlab`
- Hoja de seguimiento: `openpyxl`

## Convenciones de trabajo

- Commits en español, en imperativo: "añade vista de microciclo".
- Preferir soluciones simples. Es una web de consulta para un entrenador, no un producto.
- Antes de tocar contenido deportivo, preguntar. Antes de tocar código, adelante.
