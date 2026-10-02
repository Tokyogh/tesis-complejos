from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import func, or_

from .. import db
from ..models import ESTADOS_SOLICITUD, Cita, Cotizacion, Material
from ..security import admin_required

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

UNIDADES = ("m2", "m3", "ml", "unidad", "kg", "globo", "juego", "rollo")

SECCIONES = {"cotizaciones", "citas", "materiales", "usuarios"}


def _numero(valor, defecto=0.0):
    try:
        return float(str(valor).replace(",", ".").strip() or defecto)
    except (TypeError, ValueError):
        return float(defecto)


def _estado_valido(estado):
    return estado if estado in ESTADOS_SOLICITUD else "Pendiente"


def _texto(valor, largo=500):
    return (valor or "").strip()[:largo]


@admin_bp.route("")
@admin_required
def panel():
    seccion = request.args.get("seccion") if request.args.get("seccion") in SECCIONES else "cotizaciones"
    estado_filtro = request.args.get("estado") or ""
    if estado_filtro not in ESTADOS_SOLICITUD:
        estado_filtro = ""
    busqueda = _texto(request.args.get("q"), 80)

    base_cotizaciones = Cotizacion.query
    base_citas = Cita.query

    if estado_filtro:
        base_cotizaciones = base_cotizaciones.filter(Cotizacion.estado == estado_filtro)
        base_citas = base_citas.filter(Cita.estado == estado_filtro)

    if busqueda:
        patron = f"%{busqueda}%"
        base_cotizaciones = base_cotizaciones.filter(
            or_(Cotizacion.proyecto.ilike(patron), Cotizacion.solicitante.ilike(patron), Cotizacion.correo.ilike(patron))
        )
        base_citas = base_citas.filter(
            or_(Cita.nombre.ilike(patron), Cita.correo.ilike(patron), Cita.mensaje.ilike(patron))
        )

    cotizaciones = base_cotizaciones.order_by(Cotizacion.creada_en.desc()).all()
    citas = base_citas.order_by(Cita.creada_en.desc()).all()

    resumen = {
        "cotizaciones": Cotizacion.query.count(),
        "citas": Cita.query.count(),
        "pendientes": Cotizacion.query.filter(Cotizacion.estado == "Pendiente").count()
        + Cita.query.filter(Cita.estado == "Pendiente").count(),
        "monto": db.session.query(func.coalesce(func.sum(Cotizacion.costo_total), 0.0)).scalar() or 0.0,
        "clientes": db.session.query(func.count(func.distinct(Cotizacion.user_id))).scalar() or 0,
    }

    conteos = {estado: 0 for estado in ESTADOS_SOLICITUD}
    for estado, total in db.session.query(Cotizacion.estado, func.count(Cotizacion.id)).group_by(
        Cotizacion.estado
    ):
        conteos[estado] = conteos.get(estado, 0) + total
    for estado, total in db.session.query(Cita.estado, func.count(Cita.id)).group_by(Cita.estado):
        conteos[estado] = conteos.get(estado, 0) + total

    return render_template(
        "admin.html",
        seccion=seccion,
        cotizaciones=cotizaciones,
        citas=citas,
        resumen=resumen,
        conteos=conteos,
        estados=ESTADOS_SOLICITUD,
        estado_filtro=estado_filtro,
        busqueda=busqueda,
    )


@admin_bp.route("/usuarios")
@admin_required
def usuarios():
    from ..models import User

    lista = User.query.order_by(User.creado_en.desc()).all()
    return render_template("admin_usuarios.html", usuarios=lista, estados=ESTADOS_SOLICITUD)


@admin_bp.post("/solicitudes/<tipo>/<int:identificador>/estado")
@admin_required
def actualizar_estado(tipo, identificador):
    modelo = {"cotizacion": Cotizacion, "cita": Cita}.get(tipo)
    if modelo is None:
        flash("Tipo de solicitud desconocido.", "error")
        return redirect(url_for("admin.panel"))

    registro = db.get_or_404(modelo, identificador)
    estado = _estado_valido(_texto(request.form.get("estado"), 30))
    observaciones = _texto(request.form.get("observaciones"), 1000)

    registro.estado = estado
    registro.observaciones = observaciones
    if isinstance(registro, Cita):
        registro.atendida = estado in ("Aprobado", "Rechazado")

    db.session.commit()
    flash(f"Solicitud #{registro.id} actualizada a {estado}.", "exito")
    return redirect(request.referrer or url_for("admin.panel"))


@admin_bp.route("/materiales", methods=["GET", "POST"])
@admin_required
def materiales():
    if request.method == "POST":
        errores = _guardar_material(None)
        if not errores:
            flash("Material agregado al catálogo.", "exito")
            return redirect(url_for("admin.materiales"))
        flash("Revisa los datos del material: " + " ".join(errores.values()), "error")
        return redirect(url_for("admin.materiales"))

    categorias = sorted({material.categoria for material in Material.query.all()})
    return render_template(
        "admin_materiales.html",
        materiales=Material.query.order_by(Material.categoria.asc(), Material.nombre.asc()).all(),
        categorias=categorias,
        unidades=UNIDADES,
        errores={},
    )


@admin_bp.post("/materiales/<int:identificador>")
@admin_required
def editar_material(identificador):
    material = db.get_or_404(Material, identificador)
    errores = _guardar_material(material)
    if not errores:
        flash(f"Material «{material.nombre}» actualizado.", "exito")
    else:
        flash("Revisa los datos del material: " + " ".join(errores.values()), "error")
    return redirect(url_for("admin.materiales"))


@admin_bp.post("/materiales/<int:identificador>/eliminar")
@admin_required
def eliminar_material(identificador):
    material = db.get_or_404(Material, identificador)
    nombre = material.nombre
    db.session.delete(material)
    db.session.commit()
    flash(f"Material «{nombre}» eliminado del catálogo.", "info")
    return redirect(url_for("admin.materiales"))


def _guardar_material(material):
    datos = {
        "nombre": _texto(request.form.get("nombre"), 120),
        "clave": _texto(request.form.get("clave"), 60).lower().replace(" ", "_"),
        "unidad": _texto(request.form.get("unidad"), 30),
        "categoria": _texto(request.form.get("categoria"), 60),
        "precio": _numero(request.form.get("precio")),
        "merma": _numero(request.form.get("merma")),
        "descripcion": _texto(request.form.get("descripcion"), 600),
    }

    errores = {}
    if len(datos["nombre"]) < 3:
        errores["nombre"] = "el nombre es obligatorio"
    if not datos["clave"]:
        errores["clave"] = "la clave es obligatoria"
    if not datos["unidad"]:
        errores["unidad"] = "la unidad es obligatoria"
    if not datos["categoria"]:
        errores["categoria"] = "la categoría es obligatoria"
    if datos["precio"] < 0:
        errores["precio"] = "el precio no puede ser negativo"
    if not 0 <= datos["merma"] <= 100:
        errores["merma"] = "la merma debe estar entre 0 y 100%"

    if not errores and datos["nombre"] != (material.nombre if material else None):
        repetido = Material.query.filter(
            func.lower(Material.nombre) == datos["nombre"].lower(), Material.id != (material.id if material else -1)
        ).first()
        if repetido:
            errores["nombre"] = "ya existe un material con ese nombre"

    if not errores and datos["clave"] != (material.clave if material else None):
        repetido = Material.query.filter(
            Material.clave == datos["clave"], Material.id != (material.id if material else -1)
        ).first()
        if repetido:
            errores["clave"] = "ya existe un material con esa clave"

    if errores:
        return errores

    if material is None:
        material = Material()
        db.session.add(material)

    material.nombre = datos["nombre"]
    material.clave = datos["clave"]
    material.unidad = datos["unidad"]
    material.categoria = datos["categoria"]
    material.precio_referencial = round(datos["precio"], 2)
    material.merma_pct = round(datos["merma"], 2)
    material.descripcion = datos["descripcion"]
    db.session.commit()
    return {}
