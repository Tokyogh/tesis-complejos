import re
from datetime import date

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user

from .. import db
from ..models import Cita

contact_bp = Blueprint("contact", __name__, url_prefix="/contacto")

CORREO_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[A-Za-z]{2,}$")
TELEFONO_RE = re.compile(r"^[0-9+\s()\-]{6,25}$")

TIPOS_SERVICIO = [
    "Visita a obra",
    "Asesoría técnica",
    "Estudio de factibilidad",
    "Cotización formal",
    "Postventa y mantención",
]

DATOS_CONTACTO = {
    "telefono": "+593 2 000 0000",
    "correo": "contacto@polideportivos.ec",
    "direccion": "Av. Amazonas N34-1234, Of. 802 · Quito, Pichincha",
    "horario": "Lunes a viernes, 08:00 a 18:00 h (GMT-5)",
}


def _es_valido(fecha_texto):
    try:
        return date.fromisoformat(fecha_texto)
    except (TypeError, ValueError):
        return None


@contact_bp.route("", methods=["GET", "POST"])
def contacto():
    formulario = {
        "nombre": current_user.nombre if current_user.is_authenticated else "",
        "correo": current_user.correo if current_user.is_authenticated else "",
        "telefono": (current_user.telefono or "") if current_user.is_authenticated else "",
        "fecha": date.today().isoformat(),
        "tipo": TIPOS_SERVICIO[0],
        "mensaje": "",
    }
    errores = []

    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Crea tu cuenta o inicia sesión para enviar tu solicitud de asesoría.", "aviso")
            return redirect(url_for("auth.login", next=request.full_path))

        for campo in formulario:
            formulario[campo] = (request.form.get(campo) or "").strip()

        if not formulario["nombre"]:
            errores.append("El nombre es obligatorio.")
        if not CORREO_RE.match(formulario["correo"]):
            errores.append("Debes ingresar un correo electrónico válido.")
        if formulario["telefono"] and not TELEFONO_RE.match(formulario["telefono"]):
            errores.append("El teléfono solo puede contener números y los signos + ( ) -.")
        fecha = _es_valido(formulario["fecha"])
        if fecha is None:
            errores.append("La fecha de la visita no es válida.")
        elif fecha < date.today():
            errores.append("La fecha debe ser igual o posterior a hoy.")
        if formulario["tipo"] not in TIPOS_SERVICIO:
            errores.append("Selecciona un tipo de servicio válido.")
        if len(formulario["mensaje"]) < 10:
            errores.append("Cuéntanos brevemente el proyecto (mínimo 10 caracteres).")

        if not errores:
            cita = Cita(
                nombre=formulario["nombre"],
                correo=formulario["correo"],
                telefono=formulario["telefono"] or None,
                fecha=fecha,
                tipo=formulario["tipo"],
                mensaje=formulario["mensaje"],
                estado="Pendiente",
                user_id=current_user.id,
            )
            db.session.add(cita)
            db.session.commit()
            flash(
                f"¡Gracias {cita.nombre}! Registramos tu solicitud {tipo_resumen(cita.tipo)} para el {cita.fecha.strftime('%d/%m/%Y')}. Te contactaremos por correo.",
                "exito",
            )
            return redirect(url_for("panel.mis_solicitudes"))

    return render_template(
        "contacto.html",
        formulario=formulario,
        errores=errores,
        tipos=TIPOS_SERVICIO,
        datos=DATOS_CONTACTO,
    )


def tipo_resumen(tipo):
    resumen = {
        "Visita a obra": "de visita a obra",
        "Asesoría técnica": "de asesoría técnica",
        "Estudio de factibilidad": "de estudio de factibilidad",
        "Cotización formal": "de cotización formal",
        "Postventa y mantención": "de postventa y mantención",
    }
    return resumen.get(tipo, f"de {tipo.lower()}")
