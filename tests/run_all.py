"""Ejecuta toda la bateria de pruebas del proyecto.

Uso:
    python tests/run_all.py            # solo pruebas Python
    python tests/run_all.py --js       # incluye pruebas de navegador (requiere servidor)
    python tests/run_all.py --servidor # levanta el servidor y ejecuta tambien las de navegador
"""

import argparse
import pathlib
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
RAIZ = HERE.parent
BASE = "http://127.0.0.1:5000"

PYTHON = [
    "test_calculadora.py",
    "test_auth.py",
    "test_visual.py",
    "test_ecuador.py",
    "test_portada.py",
    "validar_proyecto.py",
]

JS = [
    "test_precios_dom.js",
    "test_csv_dom.js",
    "test_modal_dom.js",
]


def servidor_activo(timeout=1.5):
    try:
        with urllib.request.urlopen(BASE, timeout=timeout):
            return True
    except (urllib.error.URLError, socket.timeout, OSError):
        return False


def puerto_libre():
    with socket.socket() as sock:
        try:
            sock.bind(("127.0.0.1", 5000))
            return True
        except OSError:
            return False


def jsdom_disponible():
    try:
        subprocess.run(
            ["node", "-e", "require.resolve('jsdom')"],
            cwd=RAIZ,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        return True
    except (OSError, FileNotFoundError):
        return False


def ejecutar(comando, etiqueta):
    print(f"\n{'=' * 70}\n{etiqueta}\n{'=' * 70}")
    proceso = subprocess.run(comando, cwd=RAIZ, shell=isinstance(comando, str))
    return proceso.returncode == 0


def levantar_servidor():
    servidor = subprocess.Popen(
        [sys.executable, "run.py"],
        cwd=RAIZ,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        time.sleep(0.5)
        if servidor_activo():
            return servidor
    servidor.terminate()
    return None


def main():
    analizador = argparse.ArgumentParser()
    analizador.add_argument("--js", action="store_true", help="incluir pruebas de navegador")
    analizador.add_argument("--servidor", action="store_true", help="levanta el servidor para las pruebas JS")
    opciones = analizador.parse_args()

    resultados = []

    for nombre in PYTHON:
        resultados.append((nombre, ejecutar([sys.executable, f"tests/{nombre}"], f"PYTHON  {nombre}")))

    if opciones.js or opciones.servidor:
        servidor = None
        if not jsdom_disponible():
            print("\njsdom no esta instalado: se omiten las pruebas de navegador.")
            print("  npm install")
        elif opciones.servidor and not servidor_activo():
            if not puerto_libre():
                print("El puerto 5000 esta ocupado y no responde. Inicia el servidor manualmente.")
                return 1
            print("Levantando servidor de desarrollo...")
            servidor = levantar_servidor()

        if jsdom_disponible() and servidor_activo():
            for nombre in JS:
                resultados.append((nombre, ejecutar(["node", f"tests/js/{nombre}"], f"NODE    {nombre}")))
        elif jsdom_disponible():
            print("\nServidor no disponible: se omiten las pruebas de navegador.")
            print("  python tests/run_all.py --servidor")

        if servidor is not None:
            servidor.terminate()
            servidor.wait(timeout=10)

    print(f"\n{'=' * 70}")
    for nombre, ok in resultados:
        print(f"{'PASA' if ok else 'FALLA'}  {nombre}")

    fallidos = [nombre for nombre, ok in resultados if not ok]
    print(f"\n{len(resultados) - len(fallidos)}/{len(resultados)} pruebas superadas.")
    if fallidos:
        print(f"Con fallos: {', '.join(fallidos)}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
