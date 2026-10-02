"""Auditoria estatica del codigo de la aplicacion.

Revisa codificacion (BOM y glifos CJK), lineas excesivamente largas,
tabulaciones en Python, residues de la version chilena (yacute, etc.),
balance de bloques Jinja y sintaxis de los archivos .py.

Las pruebas del directorio tests/ se excluyen a proposito: contienen
cadenas de control que dispararian este mismo validador.
"""

import pathlib
import re
import sys
import unicodedata

RAIZ = pathlib.Path(__file__).resolve().parent.parent

problemas = 0

SOSPECHOSOS = ["yacute", "para_events", "de/andina", "全国", "_events", "播种", ";;", "???"]

PARES = [("block", "endblock"), ("for", "endfor"), ("if", "endif"), ("with", "endwith")]

EXCLUIDOS = {".git", "instance", "tests", "__pycache__", ".venv", "venv", "node_modules"}

for ruta in sorted(RAIZ.rglob("*")):
    if not ruta.is_file() or ruta.suffix.lower() not in {".py", ".html", ".css", ".js"}:
        continue
    if any(parte in EXCLUIDOS for parte in ruta.parts):
        continue

    texto = ruta.read_text(encoding="utf-8")
    relativo = str(ruta.relative_to(RAIZ))

    if texto.startswith("\ufeff"):
        problemas += 1
        print(f"BOM  {relativo}")

    for numero, linea in enumerate(texto.splitlines(), 1):
        if len(linea) > 200 and "http" not in linea and ruta.suffix != ".html" and not ruta.name.endswith(".min.js"):
            problemas += 1
            print(f"LONG {relativo}:{numero} ({len(linea)} car.)")

        for caracter in linea:
            if caracter == "\t" and ruta.suffix == ".py":
                problemas += 1
                print(f"TAB  {relativo}:{numero}")
                break
            if ord(caracter) > 0x2FFF or unicodedata.category(caracter) == "Cc" and caracter not in "\n\r\t":
                problemas += 1
                print(f"GLYPH {relativo}:{numero} U+{ord(caracter):04X} {unicodedata.name(caracter, '?')}")
                break

        for patron in SOSPECHOSOS:
            if patron in linea:
                problemas += 1
                print(f"SUSPECT {relativo}:{numero} -> {linea.strip()[:90]}")
                break

    if ruta.suffix == ".html":
        for apertura, cierre in PARES:
            abiertos = len(re.findall(r"{%-?\s*" + apertura + r"[\s%]", texto))
            cerrados = len(re.findall(r"{%-?\s*" + cierre + r"[\s%]", texto))
            if abiertos != cerrados:
                problemas += 1
                print(f"JINJA {relativo}: {apertura}={abiertos} vs {cierre}={cerrados}")

    if ruta.suffix == ".py":
        try:
            compile(texto, str(ruta), "exec")
        except SyntaxError as error:
            problemas += 1
            print(f"SYNTAX {relativo}: {error}")

print(f"\nProblemas: {problemas}")
sys.exit(1 if problemas else 0)