# -*- coding: utf-8 -*-
"""Genera el catálogo de ejercicios, las rutinas, los protocolos y la hoja
del jugador a partir de los markdown de fuentes/.

Nada de esto se escribe a mano en ningún sitio: si el apéndice cambia una
clave técnica, la ficha de la web cambia con él.
"""

import os
import re
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from comun import (DATOS, ErrorDeFuente, calendario, escribir, leer, limpiar, secciones,
                   sin_tildes, todas_las_tablas)

# La parte 2 del apéndice va por capítulos numerados. Cada uno cae en una de
# las capacidades por las que el brief pide poder filtrar.
CAPACIDADES = {
    'Movilidad y activación': 'movilidad',
    'Fuerza · Dominante de rodilla': 'fuerza',
    'Fuerza · Dominante de cadera': 'fuerza',
    'Empuje': 'fuerza',
    'Tracción': 'fuerza',
    'Core': 'core',
    'Tobillo y pie': 'tobillo',
    'Isométricos de tendón': 'isometricos',
    'Pliometría': 'pliometria',
    'Velocidad': 'velocidad',
    'Cambios de dirección y escalera': 'cod',
}

# Los seis campos de la ficha, tal como los nombra el apéndice y como el brief
# pide que se vean. La instrucción en voz alta va aparte porque es la que el
# entrenador lee en tres segundos con el ejercicio ya empezado.
CAMPOS = {
    'Montaje': 'montaje',
    'Ejecución': 'ejecucion',
    'Di en voz alta': 'voz_alta',
    'Error frecuente': 'error',
    'Regresión': 'regresion',
    'Progresión': 'progresion',
    'Dosis': 'dosis',
    'Prioridad': 'prioridad',
    'Por qué': 'por_que',
    'Por qué está': 'por_que',
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


def material_visual(bloque):
    """Saca los enlaces de vídeo de una ficha.

    ▶ es un enlace comprobado uno a uno y se enseña como enlace externo. 🔍 es
    un término de búsqueda porque no hay enlace estable, y se enseña como
    búsqueda. **No se convierte un 🔍 en un enlace inventado**: lo pide así el
    propio apéndice y es lo que evita mandar al entrenador a un vídeo que no es.
    """
    fuera = []
    for m in re.finditer(r'\*\*▶\*\*\s*\[([^\]]+)\]\(([^)]+)\)', bloque):
        fuera.append({'tipo': 'enlace', 'texto': limpiar(m.group(1)), 'url': m.group(2)})
    for m in re.finditer(r'\*\*🔍\*\*\s*`([^`]+)`', bloque):
        fuera.append({'tipo': 'busqueda', 'termino': m.group(1).strip()})
    return fuera


def campos_de_ficha(bloque):
    """Parte una ficha en sus campos con nombre.

    Se trocea por líneas y no por posiciones: los campos van cada uno en su
    línea, salvo regresión y progresión que comparten una, y detrás vienen el
    material visual y la prosa. Cortando solo por «**Etiqueta.**» el último
    campo se tragaba el enlace de vídeo y el párrafo final, porque «**▶**» no
    lleva punto y no servía de frontera.
    """
    campos, notas = {}, []
    for linea in bloque.split('\n'):
        cruda = linea.strip()
        if not cruda:
            continue
        if cruda.startswith(('**▶', '**🔍')):
            continue                      # lo lee material_visual
        if not cruda.startswith('**'):
            if not cruda.startswith(('#', '|', '-', '>')):
                notas.append(limpiar(cruda))
            continue
        marcas = list(re.finditer(r'\*\*([^*\n]{3,24}?)\.\*\*', cruda))
        if not marcas:
            notas.append(limpiar(cruda))
            continue
        for i, m in enumerate(marcas):
            fin_trozo = marcas[i + 1].start() if i + 1 < len(marcas) else len(cruda)
            valor = limpiar(cruda[m.end():fin_trozo])
            campo = CAMPOS.get(m.group(1).strip())
            if not campo:
                notas.append(limpiar(cruda[m.start():fin_trozo]))
                continue
            if campo == 'error':
                # «… → Corrección: …» son dos cosas distintas y se separan.
                partes = re.split(r'\s*→\s*Corrección:\s*', valor, maxsplit=1)
                campos['error'] = partes[0].rstrip(' .')
                if len(partes) > 1:
                    campos['correccion'] = partes[1]
            else:
                campos[campo] = valor

    campos['notas'] = [n for n in notas if len(n) > 20]
    return campos


def ejercicios():
    """Fichas de la parte 2 del apéndice, con el nivel que les dé el catálogo."""
    texto = leer('Apendice-movilidad-y-ejercicios.md')
    parte2 = [c for t, c in secciones(texto, 1) if t.startswith('PARTE 2')]
    if not parte2:
        raise ErrorDeFuente('no aparece la PARTE 2 del apéndice')

    fichas = {}
    for titulo, cuerpo in secciones(texto, 1):
        m = re.match(r'^\d+ · (.+)$', titulo)
        if not m:
            continue
        capacidad = CAPACIDADES.get(m.group(1).strip())
        if not capacidad:
            continue
        for nombre, bloque in secciones(cuerpo, 3):
            ficha = {
                'id': clave(nombre),
                'nombre': limpiar(nombre),
                'capacidad': capacidad,
                'grupo': m.group(1).strip(),
                'video': material_visual(bloque),
                'niveles': [],
                'origen': 'Apendice-movilidad-y-ejercicios.md',
            }
            ficha.update(campos_de_ficha(bloque))
            fichas[ficha['id']] = ficha

    if len(fichas) < 60:
        raise ErrorDeFuente('solo se han leído %d fichas del apéndice' % len(fichas))

    # El catálogo sitúa cada ejercicio en su progresión N1-N5. Se enlaza por
    # nombre y, si no hay ficha, el escalón se guarda igual con su patrón: la
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
            'grupo': 'Contenido fijo semanal',
            'ejecucion': ' · '.join(pasos),
            'contenido': pasos,
            'por_que': intro[0] if intro else None,
            'video': [],
            'niveles': [],
            'notas': [],
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
    cal = calendario()

    # Los enlaces verificados del JSON se pegan a su ficha. La clave del JSON
    # va sin tildes y con guiones bajos, así que se traduce al identificador.
    for bruto, url in cal.get('enlaces_ejercicio', {}).items():
        ident = bruto.replace('_', '-')
        if ident in fichas and not any(v.get('url') == url for v in fichas[ident]['video']):
            fichas[ident]['video'].append(
                {'tipo': 'enlace', 'texto': 'Enlace verificado', 'url': url})

    # Toda ficha acaba con algo a lo que tirar. Las que el apéndice no cubre
    # reciben una búsqueda construida con su nombre, marcada como automática:
    # no es lo mismo que un enlace comprobado y el entrenador tiene que poder
    # distinguirlo. Inventar una URL sería justo lo que el apéndice pide evitar.
    sin_material = []
    for f in fichas.values():
        if f['video']:
            continue
        sin_material.append(f['nombre'])
        f['video'].append({'tipo': 'busqueda', 'automatica': True,
                           'termino': f['nombre'] + ' ejercicio técnica'})

    escribir('ejercicios.json', {
        'aviso': 'Archivo generado por scripts/generar_contenido.py. No editar a mano.',
        'capacidades': NOMBRES_CAPACIDAD,
        'bibliotecas_video': cal.get('bibliotecas_video', {}),
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
    comprobados = sum(1 for f in fichas.values()
                      if any(v['tipo'] == 'enlace' for v in f['video']))
    curadas = sum(1 for f in fichas.values()
                  if any(v['tipo'] == 'busqueda' and not v.get('automatica')
                         for v in f['video']))
    print('material visual: %d con enlace comprobado · %d con búsqueda del apéndice '
          '· %d con búsqueda automática' % (comprobados, curadas, len(sin_material)))
    if sin_material:
        carpeta = os.path.join(os.path.dirname(DATOS), 'informes')
        os.makedirs(carpeta, exist_ok=True)
        with open(os.path.join(carpeta, 'sin-material-visual.md'), 'w', encoding='utf-8') as f:
            f.write('# Ejercicios sin material visual\n\n'
                    'Generado por `scripts/generar.py`. No editar a mano.\n\n'
                    'Estos %d ejercicios no traen ni enlace ▶ ni término 🔍 en el\n'
                    'apéndice. La web les pone una búsqueda automática con su nombre,\n'
                    'marcada como tal. Añadir un ▶ o un 🔍 en el apéndice la sustituye.\n\n'
                    % len(sin_material))
            f.write('\n'.join('- ' + n for n in sorted(sin_material)) + '\n')


if __name__ == '__main__':
    main()
