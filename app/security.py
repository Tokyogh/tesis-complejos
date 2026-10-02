from functools import wraps

from flask import abort, flash, redirect, request, url_for
from flask_login import current_user


def destino_seguro(destino, por_defecto=None):
    """Evita redirecciones abiertas limitando el destino a rutas internas."""
    if destino and destino.startswith("/") and not destino.startswith("//"):
        return destino
    return por_defecto or url_for("main.index")


def admin_required(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Inicia sesión para acceder al panel de administración.", "aviso")
            return redirect(url_for("auth.login", next=request.full_path))
        if not current_user.es_admin:
            abort(403)
        return vista(*args, **kwargs)

    return envoltorio


def solo_registrados(vista):
    @wraps(vista)
    def envoltorio(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Inicia sesión o crea tu cuenta para continuar con la solicitud.", "aviso")
            return redirect(url_for("auth.login", next=request.full_path))
        return vista(*args, **kwargs)

    return envoltorio
