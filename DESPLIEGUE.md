# Desplegar en Cloudflare Pages

La web se sirve desde **Cloudflare Pages**, que además permite decidir quién
entra con **Cloudflare Access**. GitHub Pages no sabe hacer eso: publica en
abierto o no publica.

## Ajustes del proyecto

En el panel de Cloudflare: **Workers & Pages → Create → Pages → Connect to
Git**, eliges este repositorio y rellenas:

| Campo | Valor |
|---|---|
| Production branch | `main` |
| Framework preset | None |
| Build command | `bash scripts/preparar-sitio.sh` |
| Build output directory | `_sitio` |
| Root directory | *(vacío)* |

El script deja en `_sitio/` solo la web: `index.html`, `sw.js`, `assets/` y
`data/`, más `_headers`. Fuera se quedan `fuentes/`, `entregables/`,
`scripts/` y `pruebas/`, que no hacen falta para que funcione y no tienen por
qué ser descargables desde la dirección que se le pasa al equipo.

## Quién puede entrar

**Zero Trust → Access → Applications → Add an application → Self-hosted**,
apuntando al dominio del proyecto. En las políticas defines quién pasa: una
lista de correos, un dominio entero, o acceso libre.

**Aviso que importa:** las rutas de esta web van con almohadilla
(`#/jugadores`), y lo que va detrás de `#` no llega nunca al servidor. Así que
**el control de acceso es por sitio entero, no por pantalla**. No se puede
dejar abierta la ruta de jugadores y cerrar el resto; para eso habría que
publicar la hoja del jugador como un sitio aparte.

## Apagar GitHub Pages

Mientras GitHub Pages siga activo, la web está también en
`aitor1393.github.io/PreparacionFisicaBasket/` **sin ninguna identificación**,
y el control de acceso de Cloudflare no sirve de nada.

Cuando Cloudflare esté funcionando: **Settings → Pages → Source → None**.

El flujo de trabajo no cambia: sigue siendo un push a `main`. La Action de
GitHub se queda para validar —regenera `data/`, comprueba que cuadra con
`fuentes/` y pasa las pruebas—, que es lo que de verdad aporta.
