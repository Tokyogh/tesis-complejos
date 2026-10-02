"""Utilidades compartidas por las pruebas.

Agrega la raiz del proyecto al ``sys.path`` y crea aplicaciones Flask con
una base SQLite temporal, de modo que las pruebas nunca tocan
``instance/database.db``.
"""

import io
import atexit
import os
import pathlib
import sys
import tempfile

RAIZ = pathlib.Path(__file__).resolve().parent.parent
_TEMPORALES = []
_APPS = []


def _limpiar_temporales():
    for app in _APPS:
        try:
            with app.app_context():
                from app import db

                db.session.remove()
                db.engine.dispose()
        except Exception:
            pass
    for archivo in _TEMPORALES:
        try:
            os.remove(archivo)
        except (FileNotFoundError, PermissionError):
            pass


atexit.register(_limpiar_temporales)

if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))

if hasattr(sys.stdout, "buffer"):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")


def ruta_temporal(nombre="pruebas"):
    # Mantiene la SQLite temporal dentro del proyecto, que es escribible en
    # entornos restringidos donde %TEMP% puede estar fuera del sandbox.
    descriptor, archivo = tempfile.mkstemp(
        prefix=f".polideportivo-test-{nombre}-", suffix=".db", dir=RAIZ / "instance"
    )
    os.close(descriptor)
    _TEMPORALES.append(archivo)
    return archivo


def crear_app_de_pruebas(nombre="pruebas", **configuracion):
    from app import create_app

    ajustes = {"SQLALCHEMY_DATABASE_URI": f"sqlite:///{ruta_temporal(nombre)}", "TESTING": True}
    ajustes.update(configuracion)
    app = create_app(ajustes)
    _APPS.append(app)
    return app


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
