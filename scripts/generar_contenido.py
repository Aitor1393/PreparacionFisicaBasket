# -*- coding: utf-8 -*-
"""Genera el catálogo de ejercicios, las rutinas, los protocolos y la hoja
del jugador a partir de los markdown de fuentes/.

Nada de esto se escribe a mano en ningún sitio: si el apéndice cambia una
clave técnica, la ficha de la web cambia con él.
"""

import re
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from comun import (ErrorDeFuente, escribir, leer, limpiar, secciones,
                   sin_tildes, todas_las_tablas)

# Cada apartado de la parte 2 del apéndice cae en una de las capacidades por
# las que el brief pide poder filtrar.
CAPACIDADES = {
    'Movilidad': 'movilidad',
    'Fuerza · Dominante de rodilla': 'fuerza',
    'Fuerza · Dominante de cadera': 'fuerza',
    'Empuje y tracción': 'fuerza',
    'Core': 'core',
    'Tobillo y pie': 'tobillo',
    'Isométricos de tendón': 'isometricos',
    'Pliometría': 'pliometria',
    'Velocidad': 'velocidad',
    'Cambios de dirección y escalera': 'cod',
}

NOMBRES_CAPACIDAD = {
    'movilidad': 'Movilidad', 'fuerza': 'Fuerza', 'core': 'Core',
    'tobillo': 'Tobillo y pie', 'isometricos': 'Isométricos de tendón',
    'pliometria': 'Pliometría', 'velocidad': 'Velocidad',
    'cod': 'Cambios de dirección',
}


def clave(t):
    """Identificador estable a partir del nombre del ejercicio."""
    return re.sub(r'-+', '-', re.sub(r'[^a-z0-9]+', '-', sin_tildes(t).lower())).strip('-')


def buscar_ficha(texto, fichas):
    """Busca a qué ficha corresponde un ejercicio escrito en una sesión.

    Dos pasadas. Primero, el nombre de la ficha al principio del texto, y entre
    varias gana la más larga: así «Plancha lateral con elevación 3×10» va a su
    ficha y no a «Plancha lateral». Segundo, al revés, porque las sesiones
    abrevian —dicen «Isometría de gemelo 4×30"» y la ficha es «Isometría de
    gemelo en escalón»—, pero solo si encaja **una sola** ficha: «Remo con goma
    2×12/lado» encaja con cuatro remos distintos y ahí es preferible no enlazar
    a llevar al entrenador a la ficha equivocada.
    """
    limpio = sin_tildes(limpiar(texto)).lower().lstrip('*· ')
    mejor = None
    for k, f in fichas.items():
        nombre = sin_tildes(f['nombre']).lower()
        if limpio.startswith(nombre) and (mejor is None or len(nombre) > len(mejor[1])):
            mejor = (k, nombre)
    if mejor:
        return mejor[0]

    # Nombres que en las sesiones designan una familia y no un ejercicio: hay
    # cuatro remos con goma y la sesión no dice cuál, así que no se enlaza
    # ninguno. Vale más quedarse sin enlace que mandar al entrenador a la ficha
    # equivocada un lunes por la mañana.
    GENERICOS = ('remo con goma', 'flexion', 'salidas de')

    # Se corta la dosis: lo que va desde la primera cifra ya no es el nombre.
    sin_dosis = re.split(r'\s(?=[\d×])', limpio)[0].strip(' ,.')
    if len(sin_dosis) < 6:
        return None
    if sin_dosis in GENERICOS:
        return None
    candidatos = [k for k, f in fichas.items()
                  if sin_tildes(f['nombre']).lower().startswith(sin_dosis)]
    return candidatos[0] if len(candidatos) == 1 else None


def ejercicios():
    """Fichas de la parte 2 del apéndice, con el nivel que les dé el catálogo."""
    texto = leer('Apendice-movilidad-y-ejercicios.md')
    parte2 = [c for t, c in secciones(texto, 1) if t.startswith('PARTE 2')]
    if not parte2:
        raise ErrorDeFuente('no aparece la PARTE 2 del apéndice')

    fichas = {}
    for titulo, cuerpo in secciones(parte2[0], 2):
        capacidad = CAPACIDADES.get(titulo)
        if not capacidad:
            continue
        for fila in todas_las_tablas(cuerpo)[0] if todas_las_tablas(cuerpo) else []:
            if len(fila) < 3:
                continue
            nombre = limpiar(fila[0])
            # «Clave. Error: …» viene en una sola celda y se parte en dos.
            partes = re.split(r'\bError:\s*', fila[2], maxsplit=1)
            fichas[clave(nombre)] = {
                'id': clave(nombre),
                'nombre': nombre,
                'capacidad': capacidad,
                'grupo': titulo,
                'como': limpiar(fila[1]),
                'clave': limpiar(partes[0]).rstrip(' .'),
                'error': limpiar(partes[1]) if len(partes) > 1 else None,
                'niveles': [],
                'origen': 'Apendice-movilidad-y-ejercicios.md',
            }

    # El catálogo sitúa cada ejercicio en su progresión N1-N5. Se enlaza por
    # nombre exacto y, si no, se guarda el escalón igual con su patrón: la
    # progresión es información aunque no haya ficha de ejecución.
    catalogo = leer('catalogo-ejercicios-progresiones-cadete.md')
    progresiones = []
    for titulo, cuerpo in secciones(catalogo, 3):
        if not re.match(r'^2\.\d', titulo):
            continue
        patron = titulo.split(' ', 1)[1].strip()
        for fila in (todas_las_tablas(cuerpo)[0] if todas_las_tablas(cuerpo) else []):
            if len(fila) < 2 or not re.fullmatch(r'N\d', fila[0]):
                continue
            entrada = {
                'nivel': fila[0],
                'patron': patron,
                'ejercicio': limpiar(fila[1]),
                'clave': limpiar(fila[2]) if len(fila) > 2 else None,
            }
            progresiones.append(entrada)
            k = buscar_ficha(entrada['ejercicio'], fichas)
            if k:
                entrada['ficha'] = k
                fichas[k]['niveles'].append({'nivel': fila[0], 'patron': patron})

    # Fases de pliometría, que no van por niveles sino por fases F1-F4.
    fases = []
    for titulo, cuerpo in secciones(catalogo, 2):
        if titulo.startswith('3. Pliometría'):
            for fila in todas_las_tablas(cuerpo)[0]:
                m = re.match(r'\*\*(F\d) · (.+?)\*\*', fila[0])
                if m:
                    fases.append({'fase': m.group(1), 'nombre': m.group(2),
                                  'contenido': limpiar(fila[1]),
                                  'ejemplos': limpiar(fila[2]) if len(fila) > 2 else None})
    if not fases:
        raise ErrorDeFuente('no aparecen las fases de pliometría en el catálogo')

    for titulo, cuerpo in secciones(catalogo, 3):
        if not titulo.startswith('2.8'):
            continue
        pasos = [limpiar(l[2:]) for l in cuerpo.splitlines() if l.strip().startswith('- ')]
        intro = [limpiar(p) for p in re.split(r'\n\s*\n', cuerpo)
                 if p.strip() and not p.strip().startswith(('-', '|', '#'))]
        fichas['bloque-de-tobillo'] = {
            'id': 'bloque-de-tobillo',
            'nombre': 'Bloque de tobillo',
            'capacidad': 'tobillo',
            'grupo': 'Contenido fijo del miércoles',
            'como': ' · '.join(pasos),
            'clave': intro[0] if intro else None,
            'error': None,
            'niveles': [],
            'contenido': pasos,
            'origen': 'catalogo-ejercicios-progresiones-cadete.md',
        }
    if 'bloque-de-tobillo' not in fichas:
        raise ErrorDeFuente('no aparece el bloque de tobillo en el catálogo')

    return fichas, progresiones, fases


def rutinas():
    """Las rutinas cronometradas de la parte 1 del apéndice."""
    texto = leer('Apendice-movilidad-y-ejercicios.md')
    parte1 = [c for t, c in secciones(texto, 1) if t.startswith('PARTE 1')][0]
    fuera = {}
    for titulo, cuerpo in secciones(parte1, 2):
        m = re.match(r"^Rutina (?:de (\d+)'|de regeneración)", titulo)
        if not m:
            continue
        ident = 'rutina_%s' % (m.group(1) or 'domingo')
        bloques = []
        for sub, subcuerpo in secciones(cuerpo, 3) or [(None, cuerpo)]:
            filas = todas_las_tablas(subcuerpo)
            if not filas:
                continue
            ejercicios_ = []
            grupo = None
            for fila in filas[0]:
                if len(fila) < 2:
                    continue
                if len(fila) >= 3 and fila[0].startswith('**'):
                    grupo = limpiar(fila[0])
                ejercicios_.append({
                    'grupo': grupo if len(fila) >= 3 and not fila[0].startswith('**') or fila[0].startswith('**') else None,
                    'ejercicio': limpiar(fila[1] if fila[0].startswith('**') or len(fila) < 3 else fila[0]),
                    'dosis': limpiar(fila[2] if fila[0].startswith('**') else fila[1]),
                    'tiempo': limpiar(fila[-1]) if len(fila) >= 3 and not fila[0].startswith('**') else None,
                })
            bloques.append({'nombre': sub, 'ejercicios': ejercicios_})
        fuera[ident] = {
            'id': ident,
            'titulo': titulo,
            'bloques': bloques,
            'notas': [limpiar(p) for p in re.split(r'\n\s*\n', cuerpo.split('###')[0])
                      if p.strip() and not p.strip().startswith(('|', '#'))],
            'origen': 'Apendice-movilidad-y-ejercicios.md',
        }
    if 'rutina_10' not in fuera or 'rutina_15' not in fuera:
        raise ErrorDeFuente('faltan rutinas de movilidad en el apéndice')
    return fuera


def core_por_funcion():
    """El core del catálogo va por función, no por nivel: tabla aparte."""
    for titulo, cuerpo in secciones(leer('catalogo-ejercicios-progresiones-cadete.md'), 3):
        if not titulo.startswith('2.7'):
            continue
        tablas = todas_las_tablas(cuerpo)
        return [{'funcion': limpiar(f[0]), 'N1': limpiar(f[1]),
                 'N3': limpiar(f[2]), 'N5': limpiar(f[3])}
                for f in tablas[0] if len(f) >= 4]
    raise ErrorDeFuente('no aparece el apartado de core en el catálogo')


def protocolos():
    """El protocolo de vuelta tras lesión, entero y con sus límites intactos.

    El documento separa muy a conciencia lo que es competencia médica de lo que
    no. Esa separación se conserva tal cual: se guarda el apartado «Qué es y qué
    no es este documento» como aviso, y las banderas rojas van aparte para que
    la web pueda ponerlas primero, que es lo que pide el brief.
    """
    texto = leer('Protocolo-vuelta-tras-lesion.md')
    n2 = dict(secciones(texto, 2))
    n1 = dict(secciones(texto, 1))

    aviso = [limpiar(p) for p in re.split(r'\n\s*\n', n2['Qué es y qué no es este documento'])
             if p.strip() and not p.strip().startswith('#')]

    banderas = [{'senal': limpiar(f[0]), 'porque': limpiar(f[1])}
                for f in todas_las_tablas(n2['Banderas rojas · Derivación inmediata'])[0]
                if len(f) >= 2]
    if len(banderas) < 5:
        raise ErrorDeFuente('las banderas rojas se han quedado en %d' % len(banderas))

    principios = [limpiar(p) for p in re.split(r'\n\s*\n', n2['Los cinco principios'])
                  if p.strip().startswith('**')]

    semaforo = [{'estado': limpiar(f[0]), 'puede': limpiar(f[1])}
                for f in todas_las_tablas(n2['Semáforo de decisión semanal'])[0] if len(f) >= 2]

    tests = [{'test': limpiar(f[0]), 'como': limpiar(f[1]), 'criterio': limpiar(f[2])}
             for f in todas_las_tablas(n2['Batería de tests de vuelta a competir'])[0]
             if len(f) >= 3]

    lesiones = []
    for titulo, cuerpo in secciones(n1['Protocolos por lesión'], 2):
        m = re.match(r'^(\d+) · (.+)$', titulo)
        if not m:
            continue
        tablas = todas_las_tablas(cuerpo)
        fases = []
        for tabla in tablas:
            for fila in tabla:
                if len(fila) >= 3 and re.match(r'\*\*\d', fila[0]):
                    fases.append({'fase': limpiar(fila[0]), 'contenido': limpiar(fila[1]),
                                  'criterio': limpiar(fila[2])})
        fuera_tabla = [limpiar(p) for p in re.split(r'\n\s*\n', cuerpo)
                       if p.strip() and not p.strip().startswith(('|', '#'))]
        lesiones.append({
            'numero': int(m.group(1)),
            'nombre': m.group(2).strip(),
            'id': clave(m.group(2)),
            'fases': fases,
            'tablas': [[[limpiar(c) for c in f] for f in tb] for tb in tablas if not fases],
            'notas': fuera_tabla,
        })
    if len(lesiones) != 5:
        raise ErrorDeFuente('deberían salir 5 protocolos por lesión, salen %d' % len(lesiones))

    reintegracion = [{'paso': limpiar(f[0]), 'que_hace': limpiar(f[1]), 'duracion': limpiar(f[2])}
                     for f in todas_las_tablas(n1['Reintegración a pista'])[0] if len(f) >= 3]

    def parrafos(t):
        return [limpiar(p) for p in re.split(r'\n\s*\n', t)
                if p.strip() and not p.strip().startswith(('|', '#'))]

    return {
        'aviso': aviso,
        'banderas_rojas': banderas,
        'principios': principios,
        'semaforo': semaforo,
        'tests': tests,
        'lesiones': lesiones,
        'reintegracion': reintegracion,
        'reintegracion_nota': parrafos(n1['Reintegración a pista'])[-1],
        'despues_del_alta': parrafos(n1['Después del alta']),
        'registro': parrafos(n1['Registro']),
        'origen': 'Protocolo-vuelta-tras-lesion.md',
    }


def para_jugadores(rut):
    """Lo que se comparte con los jugadores: rutina del domingo y plan de Navidad.

    El plan sale de la hoja de M3, que está delimitada en el propio documento
    entre «HOJA PARA EL JUGADOR» y «FIN DE LA HOJA». Se respeta ese corte: lo de
    fuera está escrito para el entrenador, no para ellos.
    """
    texto = leer('M3-navidad-plan.md')
    n1 = dict(secciones(texto, 1))
    if 'HOJA PARA EL JUGADOR' not in n1:
        raise ErrorDeFuente('no aparece la hoja del jugador en M3')
    hoja = n1['HOJA PARA EL JUGADOR']

    sesiones_ = []
    for titulo, cuerpo in secciones(hoja, 3):
        tablas = todas_las_tablas(cuerpo)
        if titulo.startswith('Sesión') and tablas:
            sesiones_.append({
                'titulo': titulo,
                'ejercicios': [{'ejercicio': limpiar(f[0]), 'dosis': limpiar(f[1])}
                               for f in tablas[0] if len(f) >= 2],
            })
        elif titulo == 'Tu calendario' and tablas:
            calendario_ = [{'semana': limpiar(f[0]), 'que': limpiar(f[1])}
                           for f in tablas[0] if len(f) >= 2]
    carrera = [limpiar(p) for p in re.split(r'\n\s*\n', dict(secciones(hoja, 3))['Carrera'])
               if p.strip()]
    intro = [limpiar(p) for p in re.split(r'\n\s*\n', hoja.split('###')[0])
             if p.strip() and not p.strip().startswith(('|', '#', '---'))]
    cierre = [limpiar(p) for p in re.split(r'\n\s*\n', hoja)
              if p.strip().startswith('**Si te duele')]

    return {
        'navidad': {
            'titulo': 'Plan de Navidad',
            'intro': intro,
            'sesiones': sesiones_,
            'carrera': carrera,
            'calendario': calendario_,
            'cierre': cierre,
            'origen': 'M3-navidad-plan.md',
        },
        'domingo': rut['rutina_domingo'],
    }


def main():
    fichas, progresiones, fases = ejercicios()
    rut = rutinas()
    escribir('ejercicios.json', {
        'aviso': 'Archivo generado por scripts/generar_contenido.py. No editar a mano.',
        'capacidades': NOMBRES_CAPACIDAD,
        'fichas': [fichas[k] for k in sorted(fichas)],
        'progresiones': progresiones,
        'fases_pliometria': fases,
        'core_por_funcion': core_por_funcion(),
        'rutinas': rut,
    })
    escribir('protocolos.json', protocolos())
    escribir('jugadores.json', para_jugadores(rut))
    print('%d fichas · %d escalones · %d rutinas · 5 protocolos por lesión'
          % (len(fichas), len(progresiones), len(rut)))


if __name__ == '__main__':
    main()
