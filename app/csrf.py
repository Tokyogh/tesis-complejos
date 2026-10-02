"""Proteccion CSRF para los formularios de la aplicacion.

No requiere dependencias adicionales: el token se genera con ``secrets``
y se compara en tiempo constante con ``secrets.compare_digest``.

Cada formulario POST debe incluir el campo oculto que produce
``{{ csrf_token() }}``:

    <input type="hidden" name="_csrf" value="{{ csrf_token() }}">

Se puede desactivar con ``CSRF_ENABLED = False`` (lo usan las pruebas).
"""

import secrets

from flask import abort, current_app, request, session

CLAVE_SESION = "_csrf_token"
NOMBRE_CAMPO = "_csrf"
NOMBRE_ENCABEZADO = "X-CSRF-Token"
METODOS_PROTEGIDOS = {"POST", "PUT", "PATCH", "DELETE"}


def habilitado():
    return bool(current_app.config.get("CSRF_ENABLED", True))


def generar_token():
    token = session.get(CLAVE_SESION)
    if not token:
        token = secrets.token_urlsafe(32)
        session[CLAVE_SESION] = token
    return token


def csrf_token():
    if not habilitado():
        return ""
    return generar_token()


def token_recibido():
    if request.form:
        recibido = request.form.get(NOMBRE_CAMPO)
        if recibido:
            return recibido
    return request.headers.get(NOMBRE_ENCABEZADO)


def token_valido():
    esperado = session.get(CLAVE_SESION)
    recibido = token_recibido()
    if not esperado or not recibido:
        return False
    return secrets.compare_digest(esperado, recibido)


def proteger_csrf():
    if not habilitado() or request.method not in METODOS_PROTEGIDOS:
        return None
    if request.is_json:
        # Las llamadas JSON del navegador exigen un preflight CORS, que
        # impide que un sitio tercero las dispare con credenciales.
        return None
    if not token_valido():
        abort(400)
    return None