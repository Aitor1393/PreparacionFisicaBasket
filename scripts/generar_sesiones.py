# -*- coding: utf-8 -*-
"""Convierte los markdown de sesiones en data/sesiones.json.

Una entrada por cada día de entrenamiento de las 39 semanas. Cada sesión
guarda SIEMPRE el texto original de la fuente además de los campos partidos:
si el troceado se equivoca, el entrenador sigue leyendo lo que dice el
documento, no una versión mutilada.

Tres formas de sesión, y la web las distingue porque no significan lo mismo:

  explicita  el documento detalla ese día concreto
  plantilla  el documento asigna una plantilla (A1, B2, C…) y la carga de la
             semana decide el número de series
  autonoma   no hay sesión presencial: parón, y el jugador tiene su plan
"""

import re
import sys

sys.path.insert(0, __file__.rsplit('/', 1)[0])
from comun import (DIAS, ErrorDeFuente, calendario, escribir, filas_tabla,
                   leer, limpiar, partir_ejercicios, secciones, sin_tildes,
                   todas_las_tablas)

import datetime

DIA_DE_TITULO = re.compile(r'^(Martes|Mi[ée]rcoles|Viernes)\b', re.I)
MINUTOS = re.compile(r"(\d{1,2})'")
DIA_DEL_MES = re.compile(r'^(?:Martes|Mi[ée]rcoles|Viernes)\s+(\d{1,2})\b', re.I)
PLANTILLA_EN_TITULO = re.compile(r'(?:Tipo|plantilla) ([NFCD]\d?)')
CONTACTOS = re.compile(r'\((?:~)?(\d+)(?:\s*contactos)?\)')

# Martes = MD-4, miércoles = MD-3, viernes = MD-1. Martes y miércoles son días
# consecutivos: por eso el martes lleva el trabajo neural, que exige frescura,
# y el miércoles la fuerza, que tolera fatiga previa.
MD = {'martes': 'MD-4', 'miercoles': 'MD-3', 'viernes': 'MD-1'}

# Discrepancias entre lo que dice un encabezado y lo que dice el calendario.
# Se acumulan y se enseñan al final en vez de cortar la generación: las fechas
# las manda datos-temporada.json, como fija CLAUDE.md.
AVISOS = []


def dia_de(titulo):
    m = DIA_DE_TITULO.match(titulo.strip())
    if not m:
        return None
    return sin_tildes(m.group(1)).lower()


def bloque(minutos, texto):
    """Parte una línea de contenido en un bloque de sesión.

    Guarda el texto tal cual y añade encima lo que se pueda reconocer: nombre,
    contactos de pliometría y ejercicios sueltos.
    """
    crudo = texto.strip()
    nombre, resto = None, crudo

    # Una negrita solo es el nombre del bloque si va seguida de puntuación:
    # «**Fuerza.** …», «**Pliometría F1** (~46 contactos). …». Cuando detrás
    # viene un « · » la negrita es el primer ejercicio de una lista, no un
    # título, y tratarla como título se comía el resto de la línea.
    m = re.match(r'^\*\*([^*]+?)\*\*(\s*\([^)]*\))?([.:,])?\s*(.*)$', crudo, re.S)
    if m and m.group(4) and (m.group(3) or m.group(1).rstrip().endswith(('.', ':'))):
        nombre = (m.group(1) + (m.group(2) or '')).strip(' .:,')
        resto = m.group(4).strip()
    else:
        m = re.match(r'^([^:*·]{3,40}):\s*(.+)$', crudo, re.S)
        if m:
            nombre, resto = m.group(1).strip(), m.group(2).strip()

    contactos = None
    if nombre:
        c = CONTACTOS.search(nombre)
        if c:
            contactos = int(c.group(1))
            nombre = CONTACTOS.sub('', nombre).strip(' .')

    if nombre is None and ' · ' not in crudo and '×' not in crudo:
        nombre, resto = limpiar(crudo), ''

    # Sin ' · ' no hay lista de ejercicios, sino una frase. Se guarda como
    # detalle en lugar de fabricar un ejercicio de una línea entera de prosa.
    ejercicios, detalle = [], None
    if resto:
        if ' · ' in resto:
            ejercicios = [limpiar(e) for e in partir_ejercicios(resto)]
        else:
            detalle = limpiar(resto)

    return {
        'min': minutos,
        'nombre': nombre,
        'contactos': contactos,
        'ejercicios': ejercicios,
        'detalle': detalle,
        'texto': limpiar(crudo),
    }


def bloques_de(cuerpo):
    """Saca los bloques de una sesión, venga en tabla o en lista de viñetas."""
    fuera = []
    for fila in filas_tabla(cuerpo):
        if len(fila) < 2:
            continue
        m = MINUTOS.search(fila[0])
        fuera.append(bloque(int(m.group(1)) if m else None, fila[1]))
    if fuera:
        return fuera
    for linea in cuerpo.splitlines():
        linea = linea.strip()
        if linea.startswith('- ') and not linea.startswith('- Igual que'):
            fuera.append(bloque(None, linea[2:]))
    return fuera


def notas_de(cuerpo):
    """Los párrafos sueltos de una sección: los avisos que no son ejercicios."""
    fuera = []
    for parrafo in re.split(r'\n\s*\n', cuerpo):
        p = parrafo.strip()
        if p.startswith('- Igual que'):
            fuera.append(limpiar(p[2:]))
            continue
        if not p or p.startswith(('|', '-', '#', '**Martes', '**Miércoles', '**Viernes')):
            continue
        fuera.append(limpiar(p))
    return fuera


def sesion(semana, dia, titulo, cuerpo, archivo, seccion, estado='explicita',
           plantilla=None, minutos=None, ajustes=None):
    fecha = semana[dia]
    if minutos is None:
        m = MINUTOS.search(titulo)
        minutos = int(m.group(1)) if m else 50
    if plantilla is None:
        m = PLANTILLA_EN_TITULO.search(titulo)
        plantilla = m.group(1) if m else None
    return {
        'semana': semana['semana'],
        'fecha': fecha,
        'dia': dia,
        'md': MD[dia],
        'titulo': limpiar(titulo),
        'plantilla': plantilla,
        'minutos': minutos,
        'estado': estado,
        'bloques': bloques_de(cuerpo) if cuerpo else [],
        'notas': notas_de(cuerpo) if cuerpo else [],
        'ajustes': ajustes or [],
        'origen': {'archivo': archivo, 'seccion': seccion},
    }


def comprobar_dia_del_mes(titulo, fecha, archivo=''):
    """Contrasta el día que dice el encabezado con el que dice el calendario.

    No corta la generación: el calendario de datos-temporada.json es la fuente
    para todo lo que sea fecha, así que la sesión se coloca donde él diga y la
    discrepancia se anota para enseñarla al final. Cortar aquí dejaría la web
    entera sin actualizar por una errata en un encabezado.
    """
    m = DIA_DEL_MES.match(titulo.strip())
    if m and int(m.group(1)) != datetime.date.fromisoformat(fecha).day:
        AVISOS.append('%s · «%s» no cae en %s, que es lo que dice el calendario'
                      % (archivo, limpiar(titulo), fecha))


# ---------------------------------------------------------------- plantillas

def plantillas():
    """Las plantillas de sesión con nombre propio: A1, A2, B1, B2, C y play-off.

    A1 a C salen de M4-M5, que es donde están escritas una sola vez y se usan
    en todo el tramo de mantenimiento y otra vez en M7. La de play-off sale de
    M6-M9. Los tipos A, B, C y D de M1 solo describen el reparto de minutos.
    """
    fuera = {}

    texto = leer('M4-M5-mantenimiento-sesiones.md')
    for titulo, cuerpo in secciones(texto, 2):
        m = re.match(r'^(MARTES|MI[ÉE]RCOLES|VIERNES) ([NFCD]\d?) · (.+?) · (\d{2})', titulo)
        if not m:
            continue
        fuera[m.group(2)] = {
            'id': m.group(2),
            'dia': sin_tildes(m.group(1)).lower(),
            'nombre': m.group(3).strip(),
            'minutos': int(m.group(4)),
            'bloques': bloques_de(cuerpo),
            'origen': {'archivo': 'M4-M5-mantenimiento-sesiones.md', 'seccion': titulo},
        }
    if set('N1 N2 F1 F2 C'.split()) - set(fuera):
        raise ErrorDeFuente('faltan plantillas en M4-M5: %s'
                            % (set('N1 N2 F1 F2 C'.split()) - set(fuera)))

    texto = leer('M6-M9-cierre-temporada.md')
    playoff = [c for t, c in secciones(texto, 2) if t.startswith('Plantilla de microciclo')]
    if not playoff:
        raise ErrorDeFuente('no aparece la plantilla de play-off en M6-M9')
    for titulo, cuerpo in secciones(playoff[0], 3):
        dia = dia_de(titulo)
        if not dia:
            continue
        m = MINUTOS.search(titulo)
        fuera['PO-' + dia] = {
            'id': 'PO-' + dia,
            'dia': dia,
            'nombre': 'Microciclo de play-off',
            'minutos': int(m.group(1)) if m else None,
            'bloques': bloques_de(cuerpo),
            'origen': {'archivo': 'M6-M9-cierre-temporada.md',
                       'seccion': 'Plantilla de microciclo de play-off · ' + titulo},
        }
    return fuera


def tipos_de_sesion():
    """El reparto de minutos de los tipos A, B, C y D, tal como los define M1.

    Las sesiones de M1 y M2 se escriben en viñetas y solo nombran los bloques
    con contenido: la pliometría y la fuerza, no la movilidad ni la transición.
    El reparto de aquí es lo que permite reconstruir la hora completa sin
    inventar un solo minuto.
    """
    seccion = [c for t, c in secciones(leer('M1-acumulacion-sesiones.md'), 2)
               if t == 'Tipos de sesión']
    if not seccion:
        raise ErrorDeFuente('no aparece «Tipos de sesión» en M1')
    fuera = {}
    for linea in seccion[0].splitlines():
        m = re.match(r"^\*\*([NFCD]) · (\w+)[^,]*, (\d{2})'\*\* — (.+)$", linea.strip())
        if not m:
            continue
        bloques = []
        for trozo in m.group(4).split(' · '):
            b = re.match(r"^(.+?) (\d{1,2})'$", trozo.strip())
            if not b:
                raise ErrorDeFuente('bloque ilegible en los tipos de sesión: %r' % trozo)
            bloques.append({'nombre': b.group(1).strip(), 'min': int(b.group(2))})
        fuera[m.group(1)] = {'minutos': int(m.group(3)), 'bloques': bloques,
                             'dia': sin_tildes(m.group(2)).lower()}
    if set('NFCD') - set(fuera):
        raise ErrorDeFuente('faltan tipos de sesión en M1: %s' % (set('NFCD') - set(fuera)))
    return fuera


def primera_palabra(t):
    return sin_tildes(t or '').lower().split(' ')[0].strip(' .,')


def completar_con_tipo(ses, tipos):
    """Coloca los bloques en viñeta dentro del reparto de minutos de su tipo.

    El tipo se elige por el día, no por la etiqueta del encabezado. M1 define
    que el martes es el tipo N y el miércoles el F, y esa definición es la
    fuente; cuando un encabezado dice otra cosa se anota como aviso y se sigue
    lo que dice la tabla de tipos. Los bloques que el documento no detalla
    —movilidad, transición— quedan con su nombre y sus minutos, sin ejercicios.
    """
    # Solo se deduce el tipo por el día cuando ese día tiene un único tipo
    # posible: martes es N y miércoles es F. El viernes tiene dos, C de víspera
    # y D de carga, y cuál toca lo decide el calendario, no el día, así que ahí
    # manda la etiqueta del encabezado.
    porDia = {}
    for k, v in tipos.items():
        porDia.setdefault(v.get('dia'), []).append(k)
    unicos = dict((d, ks[0]) for d, ks in porDia.items() if len(ks) == 1)
    esperado = unicos.get(ses['dia'])
    if ses['plantilla'] and esperado and ses['plantilla'] != esperado:
        AVISOS.append('%s · «%s» se etiqueta Tipo %s y el %s es el tipo %s'
                      % (ses['origen']['archivo'], ses['titulo'],
                         ses['plantilla'], ses['dia'], esperado))
    tipo = tipos.get(esperado) or tipos.get(ses['plantilla'])
    if not tipo:
        return
    sueltos = list(ses['bloques'])
    montados = []
    for hueco in tipo['bloques']:
        clave = primera_palabra(hueco['nombre'])
        elegido = next((b for b in sueltos if primera_palabra(b['nombre']) == clave), None)
        if elegido:
            sueltos.remove(elegido)
            elegido = dict(elegido, min=hueco['min'], nombre=elegido['nombre'] or hueco['nombre'])
        else:
            elegido = {'min': hueco['min'], 'nombre': hueco['nombre'], 'contactos': None,
                       'ejercicios': [], 'detalle': None, 'texto': hueco['nombre'],
                       'remite_a': ses['plantilla']}
        montados.append(elegido)
    ses['bloques'] = montados + sueltos
    ses['minutos'] = tipo['minutos']


def enlazar_rutinas(ses):
    """Enlaza el bloque de movilidad con la rutina cronometrada del apéndice.

    La de 10' dice de sí misma que «es la que aparece como movilidad y
    activación 10' en todas las sesiones de M0 a M9», así que vale para
    cualquier bloque de 10', no solo el del martes. La de 15' es la del viernes
    y la de 12' la de las reentradas.

    Los bloques de movilidad de otra duración —los 8' del miércoles, por
    ejemplo— no tienen rutina con nombre en el apéndice. No se les inventa una,
    pero se marcan como movilidad para que la web pueda llevar igualmente al
    listado de rutinas: el entrenador quiere ver los ejercicios, y quedarse sin
    nada a lo que tirar es peor.
    """
    for b in ses['bloques']:
        es_movilidad = primera_palabra(b['nombre']) in ('movilidad', 'estiramientos')
        b['es_movilidad'] = es_movilidad
        if not es_movilidad:
            b['rutina'] = None
        elif b['min'] == 10:
            b['rutina'] = 'rutina_10'
        elif b['min'] == 15 and ses['dia'] == 'viernes':
            b['rutina'] = 'rutina_15'
        elif b['min'] == 12:
            b['rutina'] = 'rutina_12'
        else:
            b['rutina'] = None


def dosis_referencia():
    """La tabla de dosis y descansos del catálogo, tal cual.

    El descanso entre series no aparece en las sesiones —ninguna lo escribe—,
    pero el catálogo lo fija por tipo de contenido. Traerlo aquí es lo que
    permite enseñarlo junto a cada bloque sin inventar ni un segundo.
    """
    for titulo, cuerpo in secciones(leer('catalogo-ejercicios-progresiones-cadete.md'), 2):
        if not titulo.startswith('9. Dosis de referencia'):
            continue
        filas = todas_las_tablas(cuerpo)[0]
        return [{'contenido': limpiar(f[0]), 'series': limpiar(f[1]),
                 'descanso': limpiar(f[2])} for f in filas if len(f) >= 3]
    raise ErrorDeFuente('no aparece la tabla de dosis de referencia en el catálogo')


# Qué filas de esa tabla le corresponden a cada bloque, por su nombre. Un bloque
# de fuerza mezcla patrones principales, unilaterales y accesorios, así que se
# le enseñan los tres y que el entrenador elija: la tabla es de referencia, no
# una prescripción por ejercicio.
DESCANSOS_POR_BLOQUE = {
    'fuerza': ('Fuerza, patrón principal', 'Fuerza, unilateral', 'Fuerza accesoria'),
    'pliometria': ('Pliometría',),
    'neuromuscular': ('Velocidad', 'COD'),
    'complementaria': ('Fuerza accesoria',),
    'core': ('Core',),
    'isometricos': ('Isométricos de tendón',),
    'velocidad': ('Velocidad',),
}


def enlazar_descansos(ses, tabla):
    porNombre = dict((d['contenido'], d) for d in tabla)
    for b in ses['bloques']:
        clave = primera_palabra(b['nombre'])
        filas = DESCANSOS_POR_BLOQUE.get(clave, ())
        b['descansos'] = [porNombre[f] for f in filas if f in porNombre]


def series_por_carga():
    """La regla de M4-M5: la carga de la semana decide cuántas series se hacen."""
    for linea in leer('M4-M5-mantenimiento-sesiones.md').splitlines():
        if 'Series según carga' in linea:
            regla = {}
            for trozo in limpiar(linea).split(' · '):
                m = re.search(r'carga (\d+) → (.+)', trozo)
                if m:
                    regla[int(m.group(1))] = m.group(2).strip(' .')
            if regla:
                return regla
    raise ErrorDeFuente('no aparece la regla de series según carga en M4-M5')


def mapa_de_plantillas(cuerpo):
    """Lee de una tabla de mapa qué plantilla toca el martes y el miércoles."""
    filas, mapa = todas_las_tablas(cuerpo), {}
    if not filas:
        return mapa
    for fila in filas[0]:
        micro = re.sub(r'\*', '', fila[0]).strip()
        if len(fila) >= 7 and re.fullmatch(r'[NFCD]\d?', fila[5]):
            mapa[micro] = {'martes': fila[5], 'miercoles': fila[6]}
    return mapa


# ------------------------------------------------------------- las 39 semanas

def por_negritas(cuerpo):
    """Sesiones escritas como línea en negrita en vez de encabezado (MC10)."""
    partes = re.split(r'^\*\*((?:Martes|Mi[ée]rcoles|Viernes)[^*]*)\*\*', cuerpo, flags=re.M)
    fuera = []
    for i in range(1, len(partes), 2):
        fuera.append((partes[i].strip(), partes[i + 1]))
    return fuera


def semanas_por_etiqueta(cal):
    fuera = {}
    for m in cal['microciclos']:
        if m['microciclo']:
            fuera[m['microciclo']] = m
    return fuera


def construir():
    cal = calendario()
    porets = semanas_por_etiqueta(cal)
    pl = plantillas()
    regla_series = series_por_carga()
    semanas = {m['semana']: dict(m, formato='presencial', sesiones=[], notas=[],
                                 origen=None) for m in cal['microciclos']}

    def añadir(sem, ses):
        comprobar_dia_del_mes(ses['titulo'], ses['fecha'], ses['origen']['archivo'])
        semanas[sem['semana']]['sesiones'].append(ses)

    def marcar(sem, archivo, seccion, notas):
        s = semanas[sem['semana']]
        s['origen'] = {'archivo': archivo, 'seccion': seccion}
        s['notas'] = notas

    # --- M0: cuatro semanas numeradas, sesiones en tabla ---------------------
    arch = 'M0-pretemporada-sesiones-v2.md'
    for titulo, cuerpo in secciones(leer(arch), 2):
        m = re.match(r'^Semana (\d) ·', titulo)
        if not m:
            continue
        sem = semanas[int(m.group(1))]
        marcar(sem, arch, titulo, notas_de(cuerpo.split('###')[0]))
        for t, c in secciones(cuerpo, 3):
            dia = dia_de(t)
            if dia:
                añadir(sem, sesion(sem, dia, t, c, arch, titulo))

    # --- M1 y M2: microciclos con etiqueta, sesiones en viñetas --------------
    for arch in ('M1-acumulacion-sesiones.md', 'M2-intensificacion-sesiones.md'):
        for titulo, cuerpo in secciones(leer(arch), 2):
            etiqueta = titulo.split(' ·')[0].strip()
            if etiqueta not in porets:
                continue
            sem = porets[etiqueta]
            marcar(sem, arch, titulo, notas_de(cuerpo.split('###')[0]))
            sub = secciones(cuerpo, 3)
            versiones = [(t, c) for t, c in sub if t.startswith('Versión')]
            if versiones:
                # MC10 trae dos versiones por el puente de la Constitución. Se
                # publica la de entrenar el martes y la otra queda como variante.
                principal = versiones[0]
                for t, c in por_negritas(principal[1]):
                    dia = dia_de(t)
                    if dia:
                        añadir(sem, sesion(sem, dia, t, c, arch, titulo))
                semanas[sem['semana']]['variantes'] = [
                    {'titulo': t, 'sesiones': [limpiar(x[0]) for x in por_negritas(c)],
                     'texto': notas_de(c)} for t, c in versiones[1:]]
            else:
                for t, c in sub:
                    dia = dia_de(t)
                    if dia:
                        añadir(sem, sesion(sem, dia, t, c, arch, titulo))

    # --- M3: tres semanas autónomas y la de reactivación ---------------------
    arch = 'M3-navidad-plan.md'
    texto = leer(arch)
    mapa_m3 = todas_las_tablas([c for t, c in secciones(texto, 2)
                                if t == 'Mapa del bloque'][0])[0]
    for fila, etiqueta in zip(mapa_m3, ('SemA', 'SemB', 'SemC', 'SemD')):
        sem = porets[etiqueta]
        if 'Autónomo' in fila[2]:
            s = semanas[sem['semana']]
            s['formato'] = 'autonomo'
            s['plan_autonomo'] = limpiar(fila[2])
            marcar(sem, arch, 'Mapa del bloque', [
                'Semana sin sesión presencial. El jugador sigue el plan de Navidad.'])
    for titulo, cuerpo in secciones(texto, 2):
        if not titulo.startswith('Semana D'):
            continue
        sem = porets['SemD']
        marcar(sem, arch, titulo, notas_de(cuerpo.split('###')[0]))
        for t, c in secciones(cuerpo, 3):
            dia = dia_de(t)
            if dia:
                añadir(sem, sesion(sem, dia, t, c, arch, titulo))
    # --- Semanas que se resuelven por plantilla ------------------------------
    def por_plantilla(sem, ident, arch, seccion, ajustes):
        base = pl[ident]
        dia = base['dia']
        fecha = sem[dia]
        semanas[sem['semana']]['sesiones'].append({
            'semana': sem['semana'],
            'fecha': fecha,
            'dia': dia,
            'md': MD[dia],
            'titulo': ('%s %s · %s' % (dia.capitalize(), ident, base['nombre'])
                       if not ident.startswith('PO-')
                       else '%s · %s' % (dia.capitalize(), base['nombre'])),
            'plantilla': ident,
            'minutos': base['minutos'],
            'estado': 'plantilla',
            'bloques': [dict(b) for b in base['bloques']],
            'notas': [],
            'ajustes': ajustes,
            'origen': {'archivo': arch, 'seccion': seccion},
        })

    def ordenar(sem):
        semanas[sem['semana']]['sesiones'].sort(key=lambda s: DIAS.index(s['dia']))

    # --- M4 y M5: dos plantillas de martes y dos de miércoles, rotando -------
    arch = 'M4-M5-mantenimiento-sesiones.md'
    texto = leer(arch)
    mapa_seccion = [(t, c) for t, c in secciones(texto, 2) if t == 'Mapa del tramo'][0]
    mapa = mapa_de_plantillas(mapa_seccion[1])
    if len(mapa) != 8:
        raise ErrorDeFuente('el mapa de M4-M5 debería tener 8 microciclos, tiene %d' % len(mapa))
    for etiqueta, asignacion in mapa.items():
        sem = porets[etiqueta]
        series = regla_series.get(sem['carga'])
        if not series:
            raise ErrorDeFuente('la carga %s de %s no está en la regla de series'
                                % (sem['carga'], etiqueta))
        ajustes = ['Esta semana toca hacer %s: es lo que dice M4-M5 para una carga de %d.'
                   % (series, sem['carga'])]
        por_plantilla(sem, asignacion['martes'], arch, 'Mapa del tramo', list(ajustes))
        por_plantilla(sem, asignacion['miercoles'], arch, 'Mapa del tramo', list(ajustes))
        por_plantilla(sem, 'C', arch, 'VIERNES C · Víspera · 50\' · Todas las semanas',
                      ['El viernes es igual todas las semanas del tramo'])
        marcar(sem, arch, 'Mapa del tramo', notas_de(mapa_seccion[1]))
        ordenar(sem)

    # --- M6 a M9 -------------------------------------------------------------
    arch = 'M6-M9-cierre-temporada.md'
    texto = leer(arch)
    capitulos = dict(secciones(texto, 1))

    # M6 y M8 detallan sus microciclos; MC21 es la Semana Santa, autónoma.
    for capitulo in ('M6 · 15 marzo – 3 abril', 'M8 · 26 abril – 9 mayo · Transición'):
        for titulo, cuerpo in secciones(capitulos[capitulo], 2):
            etiqueta = titulo.split(' ·')[0].strip()
            if etiqueta not in porets:
                continue
            sem = porets[etiqueta]
            sub = [(t, c) for t, c in secciones(cuerpo, 3) if dia_de(t)]
            marcar(sem, arch, titulo, notas_de(cuerpo.split('###')[0]))
            if sub:
                for t, c in sub:
                    añadir(sem, sesion(sem, dia_de(t), t, c, arch, titulo))
            elif 'Autónomo' in titulo:
                s = semanas[sem['semana']]
                s['formato'] = 'autonomo'
                s['plan_autonomo'] = 'Tres sesiones de 25 minutos, alternando las sesiones A y B del plan de Navidad'
            else:
                # MC27 remite a plantillas en tres viñetas, una por día.
                for linea in cuerpo.splitlines():
                    m = re.match(r'^- \*\*(Martes|Mi[ée]rcoles|Viernes) \d+:\*\* (.+)$',
                                 linea.strip())
                    if not m:
                        continue
                    dia = sin_tildes(m.group(1)).lower()
                    ident = re.search(r'plantilla ([NFCD]\d?)', m.group(2))
                    if not ident:
                        raise ErrorDeFuente('«%s» no nombra plantilla' % linea.strip())
                    por_plantilla(sem, ident.group(1), arch, titulo, [limpiar(m.group(2))])
            ordenar(sem)

    # M7 reutiliza las plantillas de M4-M5 cambiando la intención, no los ejercicios.
    m7 = [c for t, c in secciones(texto, 1) if t.startswith('M7')][0]
    ajustes_m7 = [n for n in notas_de(m7) if n.startswith(('Intención', 'Series', 'Pliometría', 'Velocidad'))]
    for etiqueta, asignacion in mapa_de_plantillas(m7).items():
        sem = porets[etiqueta]
        por_plantilla(sem, asignacion['martes'], arch, 'M7', list(ajustes_m7))
        por_plantilla(sem, asignacion['miercoles'], arch, 'M7', list(ajustes_m7))
        por_plantilla(sem, 'C', arch, 'M7', list(ajustes_m7))
        marcar(sem, arch, 'M7 · 5 – 25 abril · Las cuatro jornadas decisivas',
               [n for n in notas_de(m7) if n not in ajustes_m7])
        ordenar(sem)

    # M9 usa una única plantilla de microciclo para las cuatro semanas.
    m9 = [c for t, c in secciones(texto, 1) if t.startswith('M9')][0]
    nota_final = [n for n in notas_de(m9) if n.startswith('En MC30')]
    tabla_m9 = None
    for tabla in todas_las_tablas(m9):
        # El capítulo tiene varias tablas: la de microciclos y las de la
        # plantilla de play-off. Se busca la que enumera microciclos.
        if tabla and re.fullmatch(r'\*\*MC\d+\*\*', tabla[0][0].strip()):
            tabla_m9 = tabla
            break
    if not tabla_m9:
        raise ErrorDeFuente('no aparece la tabla de microciclos de M9')
    for fila in tabla_m9:
        etiqueta = re.sub(r'\*', '', fila[0]).strip()
        if etiqueta not in porets:
            continue
        sem = porets[etiqueta]
        for dia in DIAS:
            ident = 'PO-' + dia
            ajustes = list(nota_final) if etiqueta in ('MC30', 'MC31') else []
            if dia == 'viernes':
                # La plantilla del viernes de play-off remite a la C de M4-M5.
                por_plantilla(sem, 'C', arch, 'Plantilla de microciclo de play-off',
                              ajustes + [b['texto'] for b in pl[ident]['bloques']]
                              + ['Plantilla C completa'])
            else:
                por_plantilla(sem, ident, arch, 'Plantilla de microciclo de play-off', ajustes)
        marcar(sem, arch, 'M9 · 10 mayo – 6 junio · Segunda fase',
               [n for n in notas_de(m9) if 'escenario' not in n.lower()][:3])
        ordenar(sem)

    tipos = tipos_de_sesion()
    tabla = dosis_referencia()
    for s in semanas.values():
        for ses in s['sesiones']:
            if ses['estado'] == 'explicita' and ses['plantilla']:
                completar_con_tipo(ses, tipos)
            enlazar_rutinas(ses)
            enlazar_descansos(ses, tabla)
    return semanas


# ------------------------------------------------------------ comprobaciones

def comprobar(semanas, cal):
    """Comprueba lo que tiene que cumplirse siempre. Falla en rojo si no.

    Vale más que el generador se caiga a que la web enseñe en el pabellón una
    sesión a la que le falta medio bloque.
    """
    duraciones = cal['meta']['duraciones_min']
    problemas = []

    if len(semanas) != cal['meta']['temporada']['microciclos']:
        problemas.append('hay %d semanas y deberían ser %d'
                         % (len(semanas), cal['meta']['temporada']['microciclos']))

    for n, s in sorted(semanas.items()):
        if s['formato'] == 'autonomo':
            if s['sesiones']:
                problemas.append('semana %d: es autónoma y trae sesiones' % n)
            continue
        dias = [x['dia'] for x in s['sesiones']]
        if dias != list(DIAS):
            problemas.append('semana %d: días %s' % (n, dias))
        for ses in s['sesiones']:
            esperado = duraciones[ses['dia']]
            if ses['minutos'] != esperado:
                problemas.append('%s: %d min, se esperaban %d'
                                 % (ses['fecha'], ses['minutos'], esperado))
            if not ses['bloques']:
                problemas.append('%s: sin bloques' % ses['fecha'])
            minutos = [b['min'] for b in ses['bloques']]
            if all(m is not None for m in minutos) and sum(minutos) != esperado:
                # Dos fuentes que no coinciden: los minutos de cada bloque salen
                # del markdown y la duración de la sesión del calendario. Eso se
                # arregla en el documento, no aquí, así que se avisa en vez de
                # tumbar la generación entera. Lo que sí sigue siendo fatal es
                # que una sesión no tenga bloques o le falte un día.
                AVISOS.append('%s · «%s» suma %d minutos y la sesión dura %d'
                              % (ses['origen']['archivo'], ses['titulo'],
                                 sum(minutos), esperado))

    # Los tres contenidos fijos de la temporada, según CLAUDE.md y el póster.
    # El curl nórdico entra en la semana 3, que es cuando lo introduce M0.
    def contiene(ses, aguja):
        return any(aguja in sin_tildes(x).lower()
                   for b in ses['bloques'] for x in b['ejercicios'] + [b['texto']])

    # Las dos primeras semanas de M0 son la excepción documentada: la velocidad
    # alta y el curl nórdico entran en la semana 3, no antes.
    # Los cuatro contenidos fijos del año se comprueban por semana, no por día.
    # Tras la reestructuración el bloque de tobillo cae el martes en M1 y M2 y
    # el miércoles en M4-M5, así que exigir un día concreto daría un rojo que no
    # es del generador sino de las fuentes. El día en que aparece cada uno se
    # anota como aviso, que es lo que permite verlo y decidir.
    fijos = (('velocidad', ('velocidad alta', 'velocidad progresiva')),
             ('curl nórdico', ('curl nordico',)),
             ('trabajo de tobillo', ('tobillo', 'talon')),
             ('sentadilla española', ('sentadilla espanola',)))
    for n, s in sorted(semanas.items()):
        if s['formato'] != 'presencial':
            continue
        for nombre, agujas in fijos:
            # La sentadilla española es contenido del viernes de víspera. Las
            # semanas sin partido cambian ese viernes por una sesión de carga,
            # que es otra cosa y no la lleva.
            if nombre == 'sentadilla española' and s['viernes_tipo'] != 'C':
                continue

            dias = [ses['dia'] for ses in s['sesiones']
                    if any(contiene(ses, a) for a in agujas)]

            # Un viernes que remite a la plantilla C no repite su contenido,
            # así que cuenta como que lo lleva. Este comodín es solo para eso:
            # aplicarlo a los cuatro contenidos daba por bueno cualquier día.
            if not dias and nombre == 'sentadilla española':
                if any(b.get('remite_a') == 'C'
                       for ses in s['sesiones'] for b in ses['bloques']):
                    continue

            if not dias and n >= 3:
                problemas.append('semana %d (%s): ni un día con %s'
                                 % (n, s['martes'], nombre))

            # Dos de las decisiones contrastadas de CLAUDE.md fijan el día, no
            # solo la existencia: la velocidad va el martes y el curl nórdico el
            # miércoles. Si alguna vez vuelven a cambiarse de sitio, esto lo
            # dice en rojo en vez de dejarlo pasar.
            dia_fijo = {'velocidad': 'martes', 'curl nórdico': 'miercoles'}.get(nombre)
            if dia_fijo:
                fuera = sorted(set(d for d in dias if d != dia_fijo))
                if fuera:
                    problemas.append('semana %d (%s): %s cae en %s y va el %s'
                                     % (n, s['martes'], nombre,
                                        ', '.join(fuera), dia_fijo))

    return problemas


def main():
    cal = calendario()
    semanas = construir()
    problemas = comprobar(semanas, cal)
    if problemas:
        for p in problemas:
            print('  ✗ %s' % p)
        raise ErrorDeFuente('%d comprobaciones fallidas' % len(problemas))

    salida = {
        'generado_desde': 'fuentes/ y datos-temporada.json',
        'aviso': 'Archivo generado por scripts/generar_sesiones.py. No editar a mano.',
        'meta': cal['meta'],
        'mesociclos': cal['mesociclos'],
        'plantillas': plantillas(),
        'series_por_carga': {str(k): v for k, v in series_por_carga().items()},
        'dosis_referencia': dosis_referencia(),
        'protocolo_dolor': cal['protocolo_dolor'],
        'fijos_todo_el_ano': cal['fijos_todo_el_ano'],
        'umbral_crecimiento_cm_2meses': cal['umbral_crecimiento_cm_2meses'],
        'semanas': [semanas[n] for n in sorted(semanas)],
    }
    ruta = escribir('semanas.json', salida)
    print('%d semanas · %d sesiones · %s'
          % (len(semanas), sum(len(s['sesiones']) for s in semanas.values()), ruta))
    if AVISOS:
        print('\nAVISOS DE FUENTE · el calendario y la tabla de tipos han mandado:')
        for a in sorted(set(AVISOS)):
            print('  · %s' % a)


if __name__ == '__main__':
    main()
