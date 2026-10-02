import json

from flask import Blueprint, render_template
from flask_login import current_user, login_required

from ..models import ESTADOS_SOLICITUD, Cita, Cotizacion

panel_bp = Blueprint("panel", __name__)


@panel_bp.route("/mis-solicitudes")
@login_required
def mis_solicitudes():
    cotizaciones = (
        Cotizacion.query.filter(Cotizacion.user_id == current_user.id)
        .order_by(Cotizacion.creada_en.desc())
        .all()
    )
    citas = Cita.query.filter(Cita.user_id == current_user.id).order_by(Cita.creada_en.desc()).all()

    resumen = {
        "cotizaciones": len(cotizaciones),
        "citas": len(citas),
        "pendientes": sum(1 for registro in cotizaciones + citas if registro.estado == "Pendiente"),
        "aprobadas": sum(1 for registro in cotizaciones + citas if registro.estado == "Aprobado"),
        "inversion": sum(registro.costo_total for registro in cotizaciones if registro.estado == "Aprobado"),
    }

    return render_template(
        "mis_solicitudes.html",
        cotizaciones=cotizaciones,
        citas=citas,
        resumen=resumen,
        estados=ESTADOS_SOLICITUD,
    )


def _lineas_de(cotizacion):
    try:
        lineas = json.loads(cotizacion.detalle_json or "[]")
    except (TypeError, ValueError):
        return []
    return lineas if isinstance(lineas, list) else []


@panel_bp.route("/cotizacion/<int:identificador>")
@login_required
def detalle_cotizacion(identificador):
    cotizacion = Cotizacion.query.filter(
        Cotizacion.id == identificador, Cotizacion.user_id == current_user.id
    ).first_or_404()
    return render_template(
        "detalle_cotizacion.html",
        cotizacion=cotizacion,
        lineas=_lineas_de(cotizacion),
    )
