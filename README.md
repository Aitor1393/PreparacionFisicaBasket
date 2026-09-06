# Preparación física · Cadete Masculino 2026/2027

Web de consulta de la planificación física de una temporada de baloncesto
cadete masculino. Sitio **estático**: HTML, CSS y JavaScript, sin dependencias
ni compilación, para servirlo con GitHub Pages.

El contenido deportivo ya está cerrado y validado. Este repositorio no lo
modifica: lo hace consultable desde el móvil, en el pabellón, en dos toques.

## Estado

En construcción. Ahora mismo el repositorio solo guarda las fuentes.

| | |
|---|---|
| [`CLAUDE.md`](CLAUDE.md) | Contexto del proyecto: vocabulario, restricciones y decisiones contrastadas |
| [`BRIEF-web.md`](BRIEF-web.md) | El encargo: pantallas, requisitos y criterio de aceptación |
| [`datos-temporada.json`](datos-temporada.json) | Calendario, plantillas de sesión y protocolo de dolor. Fuente de todo lo que sea carga o fecha |
| [`fuentes/`](fuentes/) | Contenido deportivo en markdown. **Única verdad** |
| [`entregables/`](entregables/) | Los documentos que hoy se entregan a jugadores y club |

## Fuentes

| Archivo | Estado |
|---|---|
| `catalogo-ejercicios-progresiones-cadete.md` | ✅ |
| `Apendice-movilidad-y-ejercicios.md` | ✅ |
| `M0-pretemporada-sesiones-v2.md` | ✅ |
| `M1-acumulacion-sesiones.md` | ⬜ falta |
| `M2-intensificacion-sesiones.md` | ✅ |
| `M3-navidad-plan.md` | ✅ |
| `M4-M5-mantenimiento-sesiones.md` | ✅ |
| `M6-M9-cierre-temporada.md` | ⬜ falta |
| `Protocolo-vuelta-tras-lesion.md` | ✅ |

Los dos que faltan sí están, como capítulos, dentro del Word de `entregables/`.

## Entregables

Los cuatro documentos que existen hoy y que la web viene a sustituir en el uso
diario:

- `planificacion-fisica-cadete-2026-27.docx` — el documento completo, 58 páginas
- `calendario-cargas-2026-27.pdf` — el póster de las 39 semanas
- `hoja-regeneracion-domingo.pdf` — la rutina del domingo, para los jugadores
- `seguimiento-carga-dolor-2026-27.xlsx` — la hoja de seguimiento

## Comprobaciones hechas sobre `datos-temporada.json`

Contrastado contra el póster de calendario: **39 semanas, sin una sola
discrepancia** en fechas, cargas ni jornadas. Todos los lunes caen en lunes y
todos los sábados son lunes + 5.

Queda una cosa por resolver, anotada para no perderla: las **etiquetas de
microciclo** del JSON no coinciden con las de los markdown a partir de la
semana 16, y `MC12` a `MC15` aparecen dos veces cada una.
