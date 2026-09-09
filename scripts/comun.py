# -*- coding: utf-8 -*-
"""Piezas compartidas por los generadores.

Todo lo que se lee sale de fuentes/ y de datos-temporada.json. Si algo no está
ahí, no existe: los generadores fallan antes que inventarlo.
"""

import json
import os
import re
import unicodedata

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FUENTES = os.path.join(RAIZ, 'fuentes')
DATOS = os.path.join(RAIZ, 'data')

DIAS = ('martes', 'miercoles', 'viernes')


class ErrorDeFuente(Exception):
    """La fuente no tiene la forma que se esperaba.

    Se lanza y se deja subir a propósito. Más vale que el generador salga en
    rojo que publicar una sesión a medias que el entrenador lea en el pabellón.
    """


def sin_tildes(t):
    return ''.join(c for c in unicodedata.normalize('NFD', t)
                   if unicodedata.category(c) != 'Mn')


def leer(nombre):
    with open(os.path.join(FUENTES, nombre), encoding='utf-8') as f:
        return f.read()


def calendario():
    with open(os.path.join(RAIZ, 'datos-temporada.json'), encoding='utf-8') as f:
        return json.load(f)


def escribir(nombre, datos):
    os.makedirs(DATOS, exist_ok=True)
    ruta = os.path.join(DATOS, nombre)
    with open(ruta, 'w', encoding='utf-8') as f:
        json.dump(datos, f, ensure_ascii=False, indent=1)
        f.write('\n')
    return ruta


def secciones(texto, nivel):
    """Parte un markdown por encabezados de un nivel dado.

    Devuelve [(titulo, cuerpo)]. El cuerpo llega hasta el siguiente encabezado
    del mismo nivel o de uno superior, nunca más allá: cortar solo por el mismo
    nivel se comería la sección siguiente cuando cambia el capítulo.
    """
    marca = '#' * nivel
    patron = re.compile(r'^(#{1,%d}) (.+)$' % nivel, re.M)
    fuera = []
    encontrados = list(patron.finditer(texto))
    for i, m in enumerate(encontrados):
        if m.group(1) != marca:
            continue
        fin = encontrados[i + 1].start() if i + 1 < len(encontrados) else len(texto)
        fuera.append((m.group(2).strip(), texto[m.end():fin]))
    return fuera


def filas_tabla(cuerpo):
    """Devuelve las filas de la primera tabla del cuerpo, sin cabecera ni guiones."""
    filas = []
    for linea in cuerpo.splitlines():
        linea = linea.strip()
        if not linea.startswith('|'):
            if filas:
                break
            continue
        celdas = [c.strip() for c in linea.strip('|').split('|')]
        if all(re.fullmatch(r':?-{2,}:?', c) for c in celdas):
            continue
        filas.append(celdas)
    return filas[1:] if filas else []


def todas_las_tablas(cuerpo):
    """Igual que filas_tabla pero devuelve una lista por cada tabla del cuerpo."""
    tablas, actual, en_tabla = [], [], False
    for linea in cuerpo.splitlines():
        linea = linea.strip()
        if linea.startswith('|'):
            celdas = [c.strip() for c in linea.strip('|').split('|')]
            if all(re.fullmatch(r':?-{2,}:?', c) for c in celdas):
                continue
            actual.append(celdas)
            en_tabla = True
        elif en_tabla:
            tablas.append(actual[1:])
            actual, en_tabla = [], False
    if en_tabla:
        tablas.append(actual[1:])
    return tablas


def limpiar(t):
    """Quita el marcado de negrita y normaliza los espacios."""
    t = re.sub(r'\*\*(.+?)\*\*', r'\1', t)
    return re.sub(r'\s+', ' ', t).strip()


def partir_ejercicios(t):
    """Parte una línea de contenido en ejercicios sueltos.

    El separador de todos los documentos es ' · '. Se parte solo por ahí: nunca
    por comas, porque muchas dosis las llevan dentro ('Escalera, 4 patrones ×2').
    """
    return [p.strip(' .') for p in t.split(' · ') if p.strip(' .')]
