import re

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from .. import db
from ..models import User
from ..security import destino_seguro

auth_bp = Blueprint("auth", __name__)

CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
TELEFONO_RE = re.compile(r"^[0-9+\s()\-]{6,25}$")

MINIMO_CLAVE = 8
LONGITUD_MAXIMA = 300


def _validar_registro(datos):
    errores = {}

    nombre = datos["nombre"]
    if len(nombre) < 3:
        errores["nombre"] = "Escribe tu nombre y apellido (mínimo 3 caracteres)."
    elif len(nombre) > 120:
        errores["nombre"] = "El nombre no puede superar los 120 caracteres."

    correo = datos["correo"]
    if not CORREO_RE.match(correo):
        errores["correo"] = "Ingresa un correo electrónico válido."
    elif len(correo) > LONGITUD_MAXIMA:
        errores["correo"] = "El correo es demasiado largo."
    elif User.query.filter_by(correo=correo).first():
        errores["correo"] = "Ya existe una cuenta registrada con ese correo."

    telefono = datos["telefono"]
    if telefono and not TELEFONO_RE.match(telefono):
        errores["telefono"] = "El teléfono solo admite números y los signos + ( ) -."

    organizacion = datos["organizacion"]
    if len(organizacion) > 120:
        errores["organizacion"] = "La organización no puede superar los 120 caracteres."

    clave = datos["clave"]
    if len(clave) < MINIMO_CLAVE:
        errores["clave"] = f"La contraseña debe tener al menos {MINIMO_CLAVE} caracteres."
    elif not any(caracter.isalpha() for caracter in clave) or not any(
        caracter.isdigit() for caracter in clave
    ):
        errores["clave"] = "Combina letras y números en tu contraseña."
    elif clave != datos["clave_confirmacion"]:
        errores["clave_confirmacion"] = "Las contraseñas no coinciden."

    if not datos["acepto"]:
        errores["acepto"] = "Debes aceptar los términos para crear tu cuenta."

    return errores


@auth_bp.route("/register", methods=["GET", "POST"])
@auth_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if current_user.is_authenticated:
        return redirect(url_for("panel.mis_solicitudes"))

    datos = {"nombre": "", "correo": "", "telefono": "", "organizacion": "", "acepto": False}
    errores = {}

    if request.method == "POST":
        datos = {
            "nombre": (request.form.get("nombre") or "").strip(),
            "correo": (request.form.get("correo") or "").strip().lower(),
            "telefono": (request.form.get("telefono") or "").strip(),
            "organizacion": (request.form.get("organizacion") or "").strip(),
            "clave": request.form.get("clave") or "",
            "clave_confirmacion": request.form.get("clave_confirmacion") or "",
            "acepto": bool(request.form.get("acepto")),
        }
        errores = _validar_registro(datos)

        if not errores:
            usuario = User(
                nombre=datos["nombre"],
                correo=datos["correo"],
                telefono=datos["telefono"] or None,
                organizacion=datos["organizacion"] or None,
                rol="usuario",
            )
            usuario.set_password(datos["clave"])
            usuario.registrar_acceso()
            db.session.add(usuario)
            db.session.commit()
            login_user(usuario)
            flash(f"¡Bienvenido {usuario.nombre.split()[0]}! Tu cuenta ya está activa.", "exito")
            return redirect(destino_seguro(request.args.get("next"), url_for("panel.mis_solicitudes")))

    return render_template("registro.html", datos=datos, errores=errores)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("panel.mis_solicitudes"))

    correo = ""
    recordar = True
    error = None

    if request.method == "POST":
        correo = (request.form.get("correo") or "").strip().lower()
        clave = request.form.get("clave") or ""
        recordar = bool(request.form.get("recordar"))
        usuario = User.query.filter_by(correo=correo).first()

        if usuario is None or not usuario.check_password(clave):
            error = "El correo o la contraseña no son correctos."
        elif not usuario.activo:
            error = "Tu cuenta está desactivada. Escríbenos para reactivarla."

        if error is None:
            usuario.registrar_acceso()
            db.session.commit()
            login_user(usuario, remember=recordar)
            flash(f"¡Hola de nuevo, {usuario.nombre.split()[0]}!", "exito")
            return redirect(destino_seguro(request.args.get("next"), url_for("panel.mis_solicitudes")))

    return render_template("login.html", correo=correo, recordar=recordar, error=error)


@auth_bp.route("/logout", methods=["GET", "POST"])
@login_required
def logout():
    logout_user()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("main.index"))
