# -*- coding: utf-8 -*-
"""Genera todo lo que consume la web a partir de fuentes/ y datos-temporada.json.

    python3 scripts/generar.py

Es el único punto de entrada. Sale en rojo si alguna fuente no tiene la forma
esperada, para que un cambio en los documentos no publique datos a medias.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import generar_sesiones
import generar_contenido
from comun import DATOS, escribir
from generar_contenido import buscar_ficha


def enlazar_sesiones_con_fichas():
    """Convierte cada ejercicio de cada sesión en {texto, ficha}.

    Así el entrenador puede tocar «Curl nórdico 2-3×5» en la sesión del lunes y
    llegar a cómo se ejecuta. Lo que no encuentra ficha se queda con ficha nula:
    se enseña igual, sin enlace, porque el texto de la sesión manda.
    """
    with open(os.path.join(DATOS, 'ejercicios.json'), encoding='utf-8') as f:
        fichas = {x['id']: x for x in json.load(f)['fichas']}
    with open(os.path.join(DATOS, 'semanas.json'), encoding='utf-8') as f:
        semanas = json.load(f)

    enlazados = total = 0

    def enlazar(bloques):
        nonlocal enlazados, total
        for b in bloques:
            nuevos = []
            for e in b['ejercicios']:
                texto = e if isinstance(e, str) else e['texto']
                ident = buscar_ficha(texto, fichas)
                total += 1
                enlazados += 1 if ident else 0
                nuevos.append({'texto': texto, 'ficha': ident})
            b['ejercicios'] = nuevos

    for semana in semanas['semanas']:
        for ses in semana['sesiones']:
            enlazar(ses['bloques'])
    for pl in semanas['plantillas'].values():
        enlazar(pl['bloques'])

    escribir('semanas.json', semanas)
    return enlazados, total


def main():
    generar_sesiones.main()
    generar_contenido.main()
    enlazados, total = enlazar_sesiones_con_fichas()
    print('%d de %d ejercicios de las sesiones enlazan con su ficha (%d%%)'
          % (enlazados, total, round(100 * enlazados / total)))


if __name__ == '__main__':
    main()
