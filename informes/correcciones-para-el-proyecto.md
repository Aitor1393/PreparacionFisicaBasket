# Correcciones que hay que hacer en el proyecto de planificación

Este documento es para pegárselo al proyecto que genera el contenido deportivo,
no para el repositorio de la web.

**Por qué existe.** Las correcciones de abajo se han aplicado ya tres veces en
el repositorio, y **cada exportación nueva las deshace**, porque el proyecto
sigue generando los documentos con el fallo. Mientras se arreglen solo aquí,
volverán en el siguiente zip. Hay que arreglarlas en origen.

Todas salen de contradicciones entre documentos: no son opiniones sobre el
entrenamiento, son sitios donde dos fuentes del propio proyecto dicen cosas
distintas. En cada una se indica cuál de las dos manda y por qué.

---

## 1 · El 31 de noviembre no existe

**Archivo:** `M2-intensificacion-sesiones.md`, microciclo MC9.

```diff
- ### Martes 31 nov — Tipo N (50')
+ ### Martes 1 dic — Tipo N (50')
```

MC9 va del 30 de noviembre al 6 de diciembre, y `datos-temporada.json` dice que
el martes de esa semana es el **2026-12-01**. Noviembre tiene 30 días.

---

## 2 · Once miércoles llevan la etiqueta del martes

**Archivos:** `M1-acumulacion-sesiones.md` (8 sesiones) y
`M2-intensificacion-sesiones.md` (3 sesiones).

```diff
- ### Miércoles 7 — Tipo N
+ ### Miércoles 7 — Tipo F
```

Igual en los miércoles 14, 21 y 28 de octubre; 4, 11, 18 y 25 de noviembre;
2, 9 y 16 de diciembre.

La sección «Tipos de sesión» del propio `M1` define **N para el martes y F para
el miércoles**, y el contenido de esas sesiones es fuerza. La etiqueta es lo que
está mal, no el contenido.

---

## 3 · El puente de la Constitución afecta al martes, no al miércoles

**Archivo:** `M2-intensificacion-sesiones.md`, microciclo MC10.

```diff
- **Aviso de calendario:** el miércoles 7 de diciembre cae en el puente.
+ **Aviso de calendario:** el martes 8 de diciembre, la Inmaculada, cae en el puente de la Constitución.
```

```diff
- ### Versión con entreno el miércoles
+ ### Versión con entreno el martes

- ### Versión sin entreno el miércoles
+ ### Versión sin entreno el martes
```

```diff
- No intentes meter lo del miércoles y lo del miércoles en la misma sesión completa.
+ No intentes meter lo del martes y lo del miércoles en la misma sesión completa.
```

Tres motivos, todos del propio documento:

- El 7 de diciembre de 2026 **es lunes**, no miércoles.
- El día de entrenamiento que cae en el puente es el **martes 8**, la Inmaculada.
- La «versión sin entreno» conserva una sesión de miércoles y la convierte en
  mixta recogiendo lo que se habría hecho el otro día. Solo tiene sentido si el
  día que falta es el martes.
- La frase final dice «miércoles» dos veces.

---

## 4 · MC10 y la semana D tienen el martes y el miércoles cambiados

**Archivos:** `M2-intensificacion-sesiones.md` (MC10) y `M3-navidad-plan.md`
(semana D).

En las dos, el **martes** lleva pliometría y fuerza, y el **miércoles** lo
neural. Es al revés que en las otras treinta y siete semanas, y contradice lo
que dice `CLAUDE.md`:

> «Martes y miércoles son días consecutivos. Por eso el martes lleva todo el
> trabajo neural, que exige frescura, y el miércoles toda la fuerza, que tolera
> fatiga previa. **Invertir ese orden degrada la calidad del salto y del
> sprint.**»

**Qué hay que hacer:** intercambiar el contenido de las dos sesiones en cada una
de esas dos semanas. Al hacerlo, dos detalles:

- La nota «aprovecha para preguntar uno a uno quién ha hecho el plan y quién no»
  tiene que quedarse en el **martes**, que es la primera sesión de la vuelta.
- El párrafo sobre por qué la velocidad vuelve progresiva viaja con su sesión,
  o sea al martes.

---

## 5 · Dos sesiones suman 55 minutos en una temporada de 50

**Archivos:** `M3-navidad-plan.md` (semana D) y `M6-M9-cierre-temporada.md`
(plantilla de play-off).

Las dos conservan el reparto del lunes viejo de 55 minutos:

| | bloques | suma |
|---|---|---|
| Semana D, sesión de fuerza | 12' + 10' + 28' + 5' | **55'** |
| Play-off, miércoles | 12' + 8' + 22' + 13' | **55'** |

Se han recortado los cinco minutos de la movilidad, de 12' a 7', que es lo que
se acordó. Si el criterio debe ser otro, decidlo en el proyecto: quitarlos de
otro bloque es una decisión de dosificación.

---

## 6 · El calendario repite cuatro etiquetas de microciclo

**Archivo:** `datos-temporada.json`.

`MC12`, `MC13`, `MC14` y `MC15` aparecen **dos veces cada una**: en las semanas
16 a 19 y otra vez en las 24 a 27. Y a partir de ahí el JSON va cuatro por
detrás de los markdown, que llaman `MC20` a lo que el JSON llama `MC16`.

Lo correcto, y es lo que dicen los markdown:

| Semanas | Etiqueta |
|---|---|
| 1-4 | sin etiqueta (M0 numera «Semana 1» a «Semana 4») |
| 5-15 | MC1 … MC11 |
| 16-19 | **SemA, SemB, SemC, SemD** (M3 las llama por letra, no MC) |
| 20-39 | MC12 … MC31 |

Encaja con lo que declara `CLAUDE.md`: «dentro de M1-M9 se nombran MC1-MC31».
El JSON actual se queda en MC27.

---

# Y una que NO se ha tocado, porque hace falta vuestra decisión

## 7 · En M1 y M2 la pliometría está en el miércoles

**Archivos:** `M1-acumulacion-sesiones.md` y `M2-intensificacion-sesiones.md`.
**Alcance: 11 microciclos, MC1 a MC11. 22 bloques mal colocados.**

En los once, el reparto es:

| Día | Lo que hay ahora | Lo que dicen las plantillas y `CLAUDE.md` |
|---|---|---|
| Martes | Neuromuscular + **Complementaria** | Pliometría + Neuromuscular |
| Miércoles | **Pliometría** + Fuerza | Fuerza + Complementaria |

Las plantillas N1, N2, F1 y F2 de `M4-M5` ponen la pliometría el martes y la
complementaria el miércoles. `CLAUDE.md` dice lo mismo.

**Y desde la última revisión hay una contradicción directa.** La decisión
contrastada nº 8 dice:

> «CMJ cada tres semanas, tres saltos **al empezar el martes**, antes de la
> pliometría.»

Pero la instrucción del CMJ está escrita dentro del bloque de pliometría del
**miércoles**. Las dos cosas no pueden ser ciertas a la vez.

**Qué hay que decidir:** si en M1 y M2 se intercambian los bloques de pliometría
y complementaria para que coincidan con el resto de la temporada, o si hay una
razón para que esos once microciclos vayan al revés. Si es lo primero, se puede
hacer de una vez en las 22 sesiones.

---

# Resumen para pegar

1. `M2` · «Martes 31 nov» → «Martes 1 dic».
2. `M1` y `M2` · once miércoles «Tipo N» → «Tipo F».
3. `M2` · el puente afecta al **martes 8**, no al miércoles 7; las dos versiones
   de MC10 son «con/sin entreno el martes»; la frase final dice «miércoles» dos
   veces.
4. `M2` (MC10) y `M3` (semana D) · intercambiar martes y miércoles.
5. `M3` y `M6-M9` · dos sesiones suman 55' y deben sumar 50'.
6. `datos-temporada.json` · MC12-MC15 duplicadas; semanas 16-19 son SemA-SemD y
   de la 20 en adelante van MC12 a MC31.
7. **Decisión pendiente:** en M1 y M2, ¿la pliometría va al martes?
