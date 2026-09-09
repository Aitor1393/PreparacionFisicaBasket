# Brief · Web de consulta de la planificación física

Documento de encargo. Léelo junto a `CLAUDE.md` y `datos-temporada.json`.

---

## Problema

Toda la planificación existe hoy en un Word de 58 páginas, un PDF de calendario, un Excel de seguimiento y una hoja suelta para los jugadores. El entrenador la consulta **en el pabellón, desde el móvil, con cinco minutos antes de empezar**. Un documento de 58 páginas no sirve para eso.

## Objetivo

Que el entrenador abra la web un martes por la mañana y en dos toques tenga delante la sesión de ese día, con sus ejercicios, series y repeticiones.

## Usuarios

| Usuario | Qué necesita |
|---|---|
| **Entrenador** (principal) | La sesión de hoy. Consultar cómo se ejecuta un ejercicio, con vídeo. Ver dónde está la temporada |
| **Jugadores** | La hoja del domingo y el plan de Navidad, desde el móvil |
| **Club y técnico de pista** | Ver la lógica del año y por qué el lunes es la sesión más dura |

---

## Fase 1 · Web estática

Es el alcance a construir. Sin login, sin base de datos, sin backend.

### Pantallas

**1. Hoy**
Pantalla de entrada. Calcula la fecha, localiza el microciclo en `datos-temporada.json` y muestra la sesión que toca. Si es fin de semana, muestra el partido o la rutina del domingo. Si estamos fuera de temporada, cae a la vista de calendario.

Debe verse sin desplazar: el día, el bloque, la carga de la semana, y los bloques de la sesión con sus minutos.

**2. Calendario**
Los 39 microciclos con su carga, mesociclo y jornada. Reproduce la lógica del póster: barras de carga, colores por tipo de bloque (construcción, mantenimiento, parón, fase final) y marca de las semanas sin partido. Cada microciclo lleva a su detalle.

**3. Microciclo**
Las tres sesiones de la semana, completas. Carga, contactos de pliometría, jornada.

**4. Sesión**
El detalle: bloques con minutos, ejercicios, series y repeticiones. Cada ejercicio enlaza a su ficha.

**5. Ejercicios**
Catálogo buscable y filtrable por capacidad (fuerza, pliometría, velocidad, COD, movilidad, core, tobillo, isométricos).

Cada ficha tiene seis campos, y los seis deben verse: **montaje**, **ejecución**, **instrucción en voz alta** (destacada, es la que se usa gritando desde la banda), **error frecuente con su corrección**, **regresión y progresión**, y **material visual**.

El campo de instrucción verbal merece tratamiento propio: es lo que el entrenador consulta en tres segundos con el ejercicio ya empezado. Que se lea de un vistazo.

**6. Protocolos**
Banderas rojas primero y bien visibles. Después el protocolo de dolor, y los protocolos por lesión. Debe quedar claro qué es competencia médica y qué no.

**7. Para jugadores**
Ruta aparte, sin la jerga del resto: rutina del domingo y plan de Navidad. Pensada para compartir por enlace.

### Requisitos

- **Móvil primero.** El uso real es un teléfono en un pabellón.
- **Funciona sin conexión** una vez cargada. La cobertura en pabellones es mala.
- **Imprimible.** Cada sesión debe poder salir en una hoja limpia.
- **Sin dependencias pesadas.** Contenido estático, se despliega en cualquier hosting gratuito.
- **Accesible.** Contraste alto, tipografía legible a distancia de brazo.

### Contenido

El contenido deportivo sale de los markdown de `/fuentes` y del JSON. Decide tú si conviene convertir los markdown a un formato estructurado en tiempo de compilación o consumirlos directamente; lo importante es que **no se duplique contenido a mano**, porque entonces divergen.

---

## Fase 2 · No construir todavía

Registro de RPE y dolor por parte de los jugadores desde el móvil, con paneles para el entrenador. Requiere backend, usuarios y almacenamiento.

Antes de abordarlo hay que resolver dos cosas: la protección de datos de menores, y si merece la pena, porque **el Excel actual ya cubre la necesidad** y un formulario compartido resolvería la recogida con una fracción del trabajo.

No empezar esta fase sin hablarlo.

---

## Fuera de alcance

- Contenido técnico-táctico de baloncesto. Esto es solo preparación física.
- Estadísticas de partido, resultados, clasificación.
- Vídeo de los ejercicios.
- Cualquier cosa que implique modificar el contenido deportivo.

---

## Criterio de aceptación

Un martes de febrero, el entrenador abre la web en el móvil camino del pabellón y en menos de diez segundos sabe qué sesión toca, con cuántas series y qué jugadores llevan restricción por dolor. Si eso funciona, la web está bien hecha.
