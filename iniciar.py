"""Prepara el entorno local e inicia la aplicación Flask."""

from __future__ import annotations

import argparse
import hashlib
import os
import subprocess
import sys
import venv
from pathlib import Path


ROOT = Path(__file__).resolve().parent
VENV = ROOT / ".venv"
REQUIREMENTS = ROOT / "requirements.txt"


def python_del_entorno() -> Path:
    if os.name == "nt":
        return VENV / "Scripts" / "python.exe"
    return VENV / "bin" / "python"


def preparar_entorno() -> Path:
    if sys.version_info < (3, 9):
        raise RuntimeError("Se requiere Python 3.9 o posterior. Instala Python y vuelve a ejecutar este archivo.")

    interprete = python_del_entorno()
    if not interprete.exists():
        print("Creando el entorno virtual .venv...", flush=True)
        venv.EnvBuilder(with_pip=True).create(VENV)

    huella = hashlib.sha256(REQUIREMENTS.read_bytes()).hexdigest()
    marca = VENV / ".requirements.sha256"
    if not marca.exists() or marca.read_text(encoding="utf-8").strip() != huella:
        print("Instalando o actualizando las dependencias...", flush=True)
        subprocess.run(
            [str(interprete), "-m", "pip", "install", "-r", str(REQUIREMENTS)],
            cwd=ROOT,
            check=True,
        )
        marca.write_text(huella + "\n", encoding="utf-8")

    return interprete


def main() -> int:
    parser = argparse.ArgumentParser(description="Prepara e inicia el sistema de estimación de polideportivos.")
    parser.add_argument(
        "--crear-admin",
        action="store_true",
        help="abre el asistente interactivo para crear la cuenta administradora y luego inicia la aplicación",
    )
    args = parser.parse_args()

    try:
        interprete = preparar_entorno()
    except (OSError, subprocess.CalledProcessError, RuntimeError) as error:
        print(f"No se pudo preparar el entorno: {error}", file=sys.stderr)
        print("Comprueba que Python 3.9+ esté instalado y que haya conexión a internet.", file=sys.stderr)
        return 1

    if args.crear_admin:
        resultado = subprocess.run(
            [str(interprete), "-m", "flask", "--app", "run.py", "crear-admin"], cwd=ROOT
        )
        if resultado.returncode:
            return resultado.returncode

    print("Iniciando en http://127.0.0.1:5000 (Ctrl+C para detener).", flush=True)
    return subprocess.run([str(interprete), str(ROOT / "run.py")], cwd=ROOT).returncode


if __name__ == "__main__":
    raise SystemExit(main())
