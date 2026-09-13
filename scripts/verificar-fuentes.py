#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Verifica la coherencia interna del proyecto antes de exportar.
Uso:  python3 verificar.py
Devuelve 0 si todo está bien, 1 si hay fallos.
"""
import json, re, sys, glob, os, datetime as dt, collections

BASE = os.path.dirname(os.path.abspath(__file__))
FUENTES = os.path.join(BASE, "fuentes")
fallos = []

def err(msg): fallos.append(msg)

# ---------- JSON ----------
with open(os.path.join(BASE, "datos-temporada.json"), encoding="utf-8") as f:
    D = json.load(f)
micros = D["microciclos"]

if len(micros) != 39:
    err(f"El JSON tiene {len(micros)} microciclos, deberían ser 39")

etiquetas = [m["microciclo"] for m in micros if m["microciclo"]]
dup = [k for k, v in collections.Counter(etiquetas).items() if v > 1]
if dup:
    err(f"Etiquetas de microciclo duplicadas en el JSON: {', '.join(sorted(dup))}")

esperado = [None]*4 + [f"MC{i}" for i in range(1,12)] + ["SemA","SemB","SemC","SemD"] + [f"MC{i}" for i in range(12,32)]
for i, (a, b) in enumerate(zip([m["microciclo"] for m in micros], esperado), start=1):
    if a != b:
        err(f"Semana {i}: el JSON dice {a!r}, debería ser {b!r}")
        break

jornadas = [m for m in micros if m["jornada"] and m["jornada"].startswith("J")]
if len(jornadas) != 22:
    err(f"Hay {len(jornadas)} jornadas de liga en el JSON, deberían ser 22")

# Fechas coherentes: martes = lunes+1, sábado = martes+4
for m in micros:
    ma = dt.date.fromisoformat(m["martes"])
    mi = dt.date.fromisoformat(m["miercoles"])
    vi = dt.date.fromisoformat(m["viernes"])
    sa = dt.date.fromisoformat(m["sabado"])
    if ma.weekday() != 1: err(f"Semana {m['semana']}: {m['martes']} no es martes")
    if mi != ma + dt.timedelta(days=1): err(f"Semana {m['semana']}: miércoles descuadrado")
    if vi != ma + dt.timedelta(days=3): err(f"Semana {m['semana']}: viernes descuadrado")
    if sa != ma + dt.timedelta(days=4): err(f"Semana {m['semana']}: sábado descuadrado")

# ---------- Markdown ----------
FECHAS = {}
for m in micros:
    for dia in ("martes", "miercoles", "viernes"):
        d = dt.date.fromisoformat(m[dia])
        FECHAS.setdefault(dia, set()).add((d.day, d.month))

MESES = {"ene":1,"feb":2,"mar":3,"abr":4,"may":5,"jun":6,"sep":9,"oct":10,"nov":11,"dic":12}
DIAS_MES = {1:31,2:28,3:31,4:30,5:31,6:30,7:31,8:31,9:30,10:31,11:30,12:31}

for ruta in sorted(glob.glob(os.path.join(FUENTES, "*.md"))):
    nombre = os.path.basename(ruta)
    with open(ruta, encoding="utf-8") as f:
        texto = f.read()

    # Sin referencias al lunes como día de entrenamiento
    for mm in re.finditer(r"(?i)\blunes\b", texto):
        err(f"{nombre}: aparece 'lunes' (los entrenamientos son martes, miércoles y viernes)")
        break

    # Fechas imposibles
    for mm in re.finditer(r"(\d{1,2})\s+(ene|feb|mar|abr|may|jun|sep|oct|nov|dic)\b", texto):
        d, mes = int(mm.group(1)), MESES[mm.group(2)]
        if d > DIAS_MES[mes]:
            err(f"{nombre}: fecha imposible '{mm.group(0)}'")

    # Cabeceras de sesión: el día debe casar con el tipo de plantilla
    for mm in re.finditer(r"(?m)^#{2,3}\s*\*{0,2}(Martes|Miércoles|Viernes)[^\n]*", texto):
        linea, dia = mm.group(0), mm.group(1)
        tipo = re.search(r"Tipo ([A-Z])\d?|\b([NFCD])\d\b", linea)
        if not tipo: continue
        letra = (tipo.group(1) or tipo.group(2))[0]
        ok = {"Martes": "N", "Miércoles": "F", "Viernes": ("C", "D")}[dia]
        if letra not in ok:
            err(f"{nombre}: '{linea.strip()}' — {dia} no puede llevar tipo {letra}")

    # Bloques de sesión en el día correcto
    partes = re.split(r"(?m)^(#{2,3}\s*\*{0,2}(?:Martes|Miércoles|Viernes)[^\n]*)$", texto)
    for i in range(1, len(partes), 2):
        cab, cuerpo = partes[i], partes[i+1]
        dia = re.search(r"(Martes|Miércoles|Viernes)", cab).group(1)
        tiene = lambda p: re.search(p, cuerpo, re.I)
        if dia == "Martes" and tiene(r"\*\*Fuerza\b") and not tiene(r"Tipo D|sesión de carga"):
            err(f"{nombre}: '{cab.strip()}' lleva Fuerza, y la fuerza va el miércoles")
        if dia == "Miércoles" and tiene(r"\*\*Pliometría") and not tiene(r"mixta"):
            err(f"{nombre}: '{cab.strip()}' lleva Pliometría, y la pliometría va el martes")

    # Las sesiones con tabla de minutos deben sumar 50
    for mm in re.finditer(r"(?m)^#{2,3}[^\n]*\n\n?\|\s*Min\s*\|[^\n]*\n\|[-\s|]+\n((?:\|[^\n]*\n)+)", texto):
        cab = texto[mm.start():texto.index("\n", mm.start())]
        mins = [int(x) for x in re.findall(r"^\|\s*(\d+)'", mm.group(1), re.M)]
        if mins and sum(mins) != 50:
            err(f"{nombre}: '{cab.strip()}' suma {sum(mins)}', deberían ser 50'")

# ---------- Salida ----------
if fallos:
    print(f"✗ {len(fallos)} fallo(s):\n")
    for f_ in fallos: print("  ·", f_)
    sys.exit(1)
print("✓ Sin fallos. El proyecto es coherente.")
sys.exit(0)
