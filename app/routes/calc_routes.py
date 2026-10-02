import json
import math

from flask import Blueprint, jsonify, render_template, request
from flask_login import current_user

from .. import db
from ..models import Cotizacion, Material

calc_bp = Blueprint("calc", __name__, url_prefix="/calculadora")

LIMITE_LADO = 200.0
LIMITE_ALTURA = 30.0
LIMITE_CANCHAS = 12
PORCENTAJE_INDIRECTOS_DEFECTO = 18.0

COMPONENTES = [
    {
        "clave": "terreno_compactacion",
        "etiqueta": "Terreno y fundaciones",
        "descripcion": "Desbroce, relleno y compactación del terreno de fundación.",
    },
    {
        "clave": "hormigon_premezclado",
        "etiqueta": "Losa de hormigón",
        "descripcion": "Losa de fundación en hormigón premezclado según espesor.",
    },
    {
        "clave": "malla_losa",
        "etiqueta": "Malla de refuerzo",
        "descripcion": "Malla electrosoldada como refuerzo de la losa.",
    },
    {
        "clave": "piso_deportivo",
        "etiqueta": "Piso deportivo techado",
        "descripcion": "Manta asfáltica para canchas cubiertas de alto tráfico.",
    },
    {
        "clave": "cesped_sintetico",
        "etiqueta": "Césped sintético",
        "descripcion": "Superficie de césped artificial para canchas al aire libre o techadas.",
    },
    {
        "clave": "estructura_cubierta",
        "etiqueta": "Cubierta metálica",
        "descripcion": "Estructura y cobertura para techumbre del recinto.",
    },
    {
        "clave": "portales_estructura",
        "etiqueta": "Portales estructurales",
        "descripcion": "Pórticos prefabricados con fundación cada 5 metros de desarrollo.",
    },
    {
        "clave": "malla_cerramiento",
        "etiqueta": "Cierre perimetral",
        "descripcion": "Malla metálica de protección en todo el perímetro.",
    },
    {
        "clave": "postes_cercamiento",
        "etiqueta": "Postes de cerco",
        "descripcion": "Postes de acero galvanizado cada 2,5 metros lineales.",
    },
    {
        "clave": "luminaria_led",
        "etiqueta": "Iluminación LED",
        "descripcion": "Una luminaria LED cada 100 m2 de superficie de juego.",
    },
    {
        "clave": "demarcacion",
        "etiqueta": "Pintura y demarcación",
        "descripcion": "Demarcación reglamentaria de líneas de juego.",
    },
    {
        "clave": "tablero_basquetbol",
        "etiqueta": "Tableros de básquetbol",
        "descripcion": "Dos tableros reglamentarios por cancha.",
    },
]


def _redondear(cantidad, decimales=2):
    if cantidad <= 0:
        return 0.0
    return round(cantidad, decimales)


def cantidades_por_clave(contexto, clave):
    """Devuelve la cantidad estimada de material para un componente."""
    area = contexto["area"]
    perimetro = contexto["perimetro"]
    cubierta = contexto["superficie_cubierta"]
    losa = contexto["volumen_losa"]
    tercios = contexto["terreno"]

    if clave == "terreno_compactacion":
        return _redondear(tercios)
    if clave == "hormigon_premezclado":
        return _redondear(losa)
    if clave == "malla_losa":
        return _redondear(area)
    if clave == "piso_deportivo":
        return _redondear(area)
    if clave == "cesped_sintetico":
        return _redondear(area)
    if clave == "estructura_cubierta":
        return _redondear(cubierta)
    if clave == "portales_estructura":
        return float(math.ceil(perimetro / 5.0))
    if clave == "malla_cerramiento":
        return _redondear(perimetro * contexto["altura"])
    if clave == "postes_cercamiento":
        return float(math.ceil(perimetro / 2.5))
    if clave == "luminaria_led":
        return float(max(math.ceil(area / 100.0), 1))
    if clave == "demarcacion":
        return _redondear(perimetro * 2.0)
    if clave == "tablero_basquetbol":
        return float(2 * contexto["num_canchas"])
    return 0.0


def calcular_presupuesto(datos):
    """Procesa los datos del formulario y devuelve un presupuesto preliminar desglosado."""
    largo = float(datos.get("largo") or 0)
    ancho = float(datos.get("ancho") or 0)
    altura = float(datos.get("altura") or 8)
    espesor_losa = float(datos.get("espesor_losa") or 0.15)
    num_canchas = int(float(datos.get("num_canchas") or 1))
    indirectos = float(datos.get("indirectos") or PORCENTAJE_INDIRECTOS_DEFECTO)

    area = _redondear(largo * ancho * num_canchas)
    perimetro = _redondear(2 * (largo + ancho) * num_canchas)

    contexto = {
        "largo": largo,
        "ancho": ancho,
        "altura": altura,
        "espesor_losa": espesor_losa,
        "num_canchas": num_canchas,
        "area": area,
        "perimetro": perimetro,
        "superficie_cubierta": _redondear(area * 1.1),
        "volumen_losa": _redondear(area * espesor_losa),
        "terreno": _redondear(area * espesor_losa * 1.5),
    }

    claves = datos.get("componentes") or []
    if isinstance(claves, str):
        claves = [claves]

    materiales = {
        material.clave: material for material in Material.query.filter(Material.clave.in_(claves)).all()
    }

    lineas = []
    for componente in COMPONENTES:
        clave = componente["clave"]
        if clave not in claves or clave not in materiales:
            continue
        material = materiales[clave]
        cantidad_base = cantidades_por_clave(contexto, clave)
        if cantidad_base <= 0:
            continue
        cantidad = _redondear(cantidad_base * (1 + (material.merma_pct or 0) / 100), 2)
        if clave in ("portales_estructura", "postes_cercamiento", "luminaria_led", "tablero_basquetbol"):
            cantidad = float(math.ceil(cantidad))
        subtotal = cantidad * material.precio_referencial
        lineas.append(
            {
                "clave": clave,
                "etiqueta": componente["etiqueta"],
                "material": material.nombre,
                "unidad": material.unidad,
                "cantidad": cantidad,
                "precio_unitario": material.precio_referencial,
                "merma_pct": material.merma_pct or 0.0,
                "subtotal": round(subtotal, 0),
            }
        )

    costo_directo = round(sum(linea["subtotal"] for linea in lineas), 0)
    monto_indirectos = round(costo_directo * indirectos / 100, 0)
    costo_total = round(costo_directo + monto_indirectos, 0)

    if area > 0 and costo_total > 0:
        costo_m2 = round(costo_total / area, 0)
    else:
        costo_m2 = 0.0

    return {
        "lineas": lineas,
        "parametros": contexto,
        "costo_directo": costo_directo,
        "porcentaje_indirectos": indirectos,
        "monto_indirectos": monto_indirectos,
        "costo_total": costo_total,
        "costo_m2": costo_m2,
    }


def _parse_datos(origen):
    return {
        "largo": origen.get("largo"),
        "ancho": origen.get("ancho"),
        "altura": origen.get("altura") or 8,
        "espesor_losa": origen.get("espesor_losa") or 0.15,
        "num_canchas": origen.get("num_canchas") or 1,
        "indirectos": origen.get("indirectos") or PORCENTAJE_INDIRECTOS_DEFECTO,
        "componentes": origen.getlist("componentes") if hasattr(origen, "getlist") else origen.get("componentes"),
    }


def validar_datos(datos):
    errores = []
    try:
        largo = float(datos.get("largo") or 0)
        ancho = float(datos.get("ancho") or 0)
        altura = float(datos.get("altura") or 0)
        espesor = float(datos.get("espesor_losa") or 0)
        canchas = int(float(datos.get("num_canchas") or 0))
        indirectos = float(datos.get("indirectos") or 0)
    except (TypeError, ValueError):
        return ["Los valores ingresados no son numéricos válidos."]

    if largo <= 0 or ancho <= 0:
        errores.append("El largo y el ancho deben ser mayores a cero.")
    if largo > LIMITE_LADO or ancho > LIMITE_LADO:
        errores.append("El largo y el ancho no pueden superar 200 metros.")
    if not 2.0 <= altura <= LIMITE_ALTURA:
        errores.append("La altura debe estar entre 2 y 30 metros.")
    if not 0.05 <= espesor <= 0.60:
        errores.append("El espesor de la losa debe estar entre 0,05 y 0,60 metros.")
    if not 1 <= canchas <= LIMITE_CANCHAS:
        errores.append("La cantidad de canchas debe estar entre 1 y 12.")
    if not 0 <= indirectos <= 100:
        errores.append("El porcentaje de gastos indirectos debe estar entre 0 y 100%.")
    if not datos.get("componentes"):
        errores.append("Debes seleccionar al menos un componente a estimar.")
    return errores


@calc_bp.route("", methods=["GET", "POST"])
def calculadora():
    errores = []
    presupuesto = None
    datos_formulario = {
        "largo": 28.0,
        "ancho": 15.0,
        "altura": 8.0,
        "espesor_losa": 0.15,
        "num_canchas": 2,
        "indirectos": PORCENTAJE_INDIRECTOS_DEFECTO,
        "componentes": [comp["clave"] for comp in COMPONENTES],
    }
    proyecto = ""
    solicitante = current_user.nombre if current_user.is_authenticated else ""
    correo = current_user.correo if current_user.is_authenticated else ""
    guardado = False

    if request.method == "POST":
        proyecto = (request.form.get("proyecto") or "").strip()
        solicitante = (request.form.get("solicitante") or "").strip() or solicitante
        correo = (request.form.get("correo") or "").strip() or correo
        datos = _parse_datos(request.form)
        datos_formulario = datos
        errores = validar_datos(datos)

        if not errores:
            presupuesto = calcular_presupuesto(datos)
            parametros = presupuesto["parametros"]
            cotizacion = Cotizacion(
                proyecto=proyecto or "Proyecto sin nombre",
                solicitante=solicitante or None,
                correo=correo or None,
                largo=parametros["largo"],
                ancho=parametros["ancho"],
                altura=parametros["altura"],
                num_canchas=parametros["num_canchas"],
                superficie=parametros["area"],
                costo_directo=presupuesto["costo_directo"],
                costo_total=presupuesto["costo_total"],
                detalle_json=json.dumps(presupuesto["lineas"], ensure_ascii=False),
                estado="Pendiente",
                user_id=current_user.id if current_user.is_authenticated else None,
            )
            db.session.add(cotizacion)
            db.session.commit()
            guardado = current_user.is_authenticated

    return render_template(
        "calculadora.html",
        componentes=COMPONENTES,
        errores=errores,
        presupuesto=presupuesto,
        datos=datos_formulario,
        proyecto=proyecto,
        solicitante=solicitante,
        correo=correo,
        indirectos_defecto=PORCENTAJE_INDIRECTOS_DEFECTO,
        guardado=guardado,
    )


@calc_bp.post("/api/estimar")
def api_estimar():
    datos = _parse_datos(request.get_json(silent=True) or request.form or {})
    if isinstance(datos.get("componentes"), str):
        datos["componentes"] = [datos["componentes"]]
    errores = validar_datos(datos)
    if errores:
        return jsonify({"ok": False, "errores": errores}), 400
    return jsonify({"ok": True, "presupuesto": calcular_presupuesto(datos)})