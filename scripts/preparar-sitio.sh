#!/usr/bin/env bash
# Arma en _sitio/ lo único que se publica.
#
# Lo usan la Action de GitHub Pages y la compilación de Cloudflare Pages, para
# que no haya dos listas de «qué se publica» que puedan separarse. Fuera se
# quedan fuentes/, entregables/, scripts/ y pruebas/: no hacen falta para que
# la web funcione y no tienen por qué ser descargables desde la dirección que
# se le pasa al equipo.
set -euo pipefail

raiz="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$raiz"

rm -rf _sitio
mkdir -p _sitio
cp -r index.html sw.js assets data _sitio/
cp _headers _sitio/
touch _sitio/.nojekyll

echo "Se publica:"
find _sitio -type f | sort
echo "Total: $(du -sh _sitio | cut -f1)"
