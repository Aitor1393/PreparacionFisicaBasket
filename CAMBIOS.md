# CAMBIOS

Qué ha cambiado respecto a la versión con la que se construyó la web. **Léelo antes de tocar nada**: hay un cambio estructural que afecta a todas las pantallas.

---

## 1 · Los días de entrenamiento han cambiado · ESTRUCTURAL

**Antes:** lunes, miércoles y viernes. Lunes 55 min, miércoles y viernes 50.
**Ahora:** **martes, miércoles y viernes. 50 minutos los tres días.**

Martes y miércoles son consecutivos, lo que obligó a reorganizar los contenidos:

| Día | Posición | Contenido | Antes estaba en |
|---|---|---|---|
| **Martes** | MD-4 | Todo el trabajo neural: pliometría, velocidad, cambios de dirección | Repartido entre lunes y miércoles |
| **Miércoles** | MD-3 | Toda la fuerza: principal y complementaria | Repartido entre lunes y miércoles |
| **Viernes** | MD-1 | Víspera, sin cambios | Igual |

**Las plantillas se han renombrado.** Si la web usa los identificadores antiguos, hay que mapearlos:

| Antes | Ahora | Día |
|---|---|---|
| A1 | **N1** | Martes, neural reactivo |
| A2 | **N2** | Martes, neural aceleración |
| B1 | **F1** | Miércoles, fuerza dominante de rodilla |
| B2 | **F2** | Miércoles, fuerza dominante de cadera |
| C | C | Viernes, víspera |
| D | D | Viernes de carga |

**Las fechas de sesión se han desplazado un día.** Lo que era "Lunes 5 de octubre" ahora es "Martes 6". El calendario de microciclos y las jornadas del sábado **no cambian**.

En `datos-temporada.json` cada microciclo trae ahora los tres campos `martes`, `miercoles` y `viernes` con la fecha exacta, además de `sabado`.

## 2 · Los contenidos fijos cambian de día

| Contenido | Antes | Ahora |
|---|---|---|
| Velocidad alta | Miércoles | **Martes** |
| Curl nórdico | Lunes | **Miércoles** |
| Bloque de tobillo | Miércoles | Miércoles |
| Sentadilla española | Viernes | Viernes |

## 3 · El apéndice de ejercicios se ha reescrito entero

Antes era una tabla de tres columnas. Ahora cada ejercicio tiene **seis campos** y los seis deben mostrarse en la ficha:

1. **Montaje**
2. **Ejecución**
3. **Instrucción en voz alta** — merece tratamiento visual propio. Es lo que el entrenador lee en tres segundos con el ejercicio ya empezado, gritando desde la banda. Que se vea de un vistazo.
4. **Error frecuente** con su corrección
5. **Regresión y progresión**
6. **Material visual**

El archivo pasa de 12.000 a 37.000 caracteres. Son 91 fichas.

**Sobre el material visual:** **▶** marca enlace verificado, **🔍** marca término de búsqueda. Los 🔍 se renderizan como botón que abre el buscador con ese término exacto. **No los conviertas en enlaces directos inventados.** Los enlaces verificados y las cinco bibliotecas de referencia están también en el JSON, en `enlaces_ejercicio` y `bibliotecas_video`.

## 4 · Nuevos datos estructurados en el JSON

- `semanas_cmj` — Semanas en que se mide el salto vertical: 2, 5, 8, 11, 14, 20, 23, 26, 28, 31, 34 y 37. Tres saltos al empezar el martes.
- `semanas_intermitente_equipo` — Semanas con acondicionamiento para todo el equipo: 5, 8, 13, 28 y 34. Siempre en el viernes de carga.
- `semanas_aceleracion_resistida` — 5, 7, 8, 11, 13 y 28.
- `progresion_velocidad_alta` — Distancia y repeticiones del sprint por semana. **Ya no es un valor fijo**: sube en las ventanas de carga y se congela en el bloque denso de febrero. Si la web mostraba un valor constante, hay que sustituirlo por este mapa.
- `intermitente_postpartido_umbral_min` — 15 minutos. Por debajo de eso, el jugador hace bloque intermitente tras el partido.

## 5 · Correcciones de contenido

- **Umbral de crecimiento: 1,2 cm** entre mediciones de dos meses, no 2 cm. Equivale a 7,2 cm al año.
- **Sentadilla española:** se ha retirado la afirmación de que reduce el dolor. Se usa porque aporta carga tolerable en competición. Si la web mostraba el texto antiguo, hay que actualizarlo.
- **Descanso del sprint: 3 minutos**, no 2.
- **Rutina del domingo:** rehecha. Ya no es una rutina de estiramientos sino movilidad, automasaje y respiración, y dura 20 minutos. Lleva una advertencia explícita de que no previene lesiones.
- **Protocolo de Sever** añadido, es el apartado 4 del documento de lesiones. Los apartados posteriores se han renumerado.
- **Esguince de tobillo:** añadidos plazos orientativos por grado y el apartado de tobilleras.
- **Ligamento cruzado:** añadidos los plazos de 9 a 12 meses.

## 6 · Sin cambios

El calendario de 39 microciclos, las fechas de las 22 jornadas, los índices de carga, los contactos de pliometría y la estructura de mesociclos M0-M9 son idénticos. Si la web ya los renderiza bien, no hay que tocarlos.

---

## Orden sugerido para la actualización

1. Mapear las plantillas A1/A2/B1/B2 a N1/N2/F1/F2 y corregir el día de cada sesión.
2. Recalcular las fechas de sesión desde los campos `martes`, `miercoles` y `viernes` del JSON.
3. Rehacer la ficha de ejercicio para los seis campos, con el botón de búsqueda para los 🔍.
4. Añadir los indicadores nuevos: CMJ, intermitente, progresión de velocidad.
5. Revisar los textos afectados por las correcciones del punto 5.

La pantalla "Hoy" es la que más cambia: ahora el lunes no hay sesión.
