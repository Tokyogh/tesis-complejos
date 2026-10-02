"""Utilidades compartidas por las pruebas.

Agrega la raiz del proyecto al ``sys.path`` y crea aplicaciones Flask con
una base SQLite temporal, de modo que las pruebas nunca tocan
``instance/database.db``.
"""

import io
import os
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def ruta_temporal(nombre="pruebas"):
    return os.path.join(tempfile.mkdtemp(prefix="polideportivo-"), f"{nombre}.db")


def crear_app_de_pruebas(nombre="pruebas", **configuracion):
    from app import create_app

    ajustes = {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta_temporal(nombre)}", "TESTING": True}
    ajustes.update(configuracion)
    return create_app(ajustes)


def componentes_de_prueba(app):
    with app.app_context():
        from app.models import Material

        claves = [material.clave for material in Material.query.all()]

    datos = {
        "proyecto": "Polideportivo Test",
        "solicitante": "Ana Pérez",
        "correo": "ana@ejemplo.ec",
        "largo": "28",
        "ancho": "15",
        "altura": "8",
        "espesor_losa": "0.15",
        "num_canchas": "2",
        "indirectos": "18",
        "componentes": claves,
    }
    return datos


def credenciales_admin(correo="admin@pruebas.ec", clave="AdminPruebas2026"):
    return {"nombre": "Administrador de Pruebas", "correo": correo, "clave": clave}


def credenciales_cliente(nombre="Cliente Prueba", correo="cliente@pruebas.ec", clave="Polideportivo2026"):
    return {
        "nombre": nombre,
        "correo": correo,
        "telefono": "+593 9 9999 0000",
        "organizacion": "Municipio de Pruebas",
        "clave": clave,
        "clave_confirmacion": clave,
        "acepto": "1",
    }
