from flask import Blueprint, render_template, request

from ..models import Material

main_bp = Blueprint("main", __name__)

IMAGENES = {
    "hero": "https://images.unsplash.com/photo-1503387762-592deb58ef4e?auto=format&fit=crop&w=2000&q=75",
    "cancha": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?auto=format&fit=crop&w=800&q=75",
}

IMAGENES_MATERIALES = {
    "terreno_compactacion": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/Excavator_performs_earth_digging.jpg/1280px-Excavator_performs_earth_digging.jpg",
        "licencia": "Dominio público",
        "fuente": "Wikimedia Commons",
    },
    "hormigon_premezclado": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/16/CAMC_concrete_mixer_truck_Xing_Kaima._Spielvogel_2.jpg/1280px-CAMC_concrete_mixer_truck_Xing_Kaima._Spielvogel_2.jpg",
        "licencia": "CC0",
        "fuente": "Wikimedia Commons",
    },
    "malla_losa": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Fer_%C3%A0_b%C3%A9ton_FerraillageReinforcement.jpg/1280px-Fer_%C3%A0_b%C3%A9ton_FerraillageReinforcement.jpg",
        "licencia": "CC BY-SA 3.0",
        "fuente": "Wikimedia Commons",
    },
    "piso_deportivo": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/8/83/Ligget_Hall_Gymnasium_IMG_4556.jpg/1280px-Ligget_Hall_Gymnasium_IMG_4556.jpg",
        "licencia": "CC BY-SA 4.0",
        "fuente": "Wikimedia Commons",
    },
    "cesped_sintetico": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/9/99/Artificial_grass_playground_%E2%80%93_Brezovec_-_Doln%C3%BD_Kub%C3%ADn_01.jpg/1280px-Artificial_grass_playground_%E2%80%93_Brezovec_-_Doln%C3%BD_Kub%C3%ADn_01.jpg",
        "licencia": "CC BY-SA 4.0",
        "fuente": "Wikimedia Commons",
    },
    "estructura_cubierta": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/3e/Modern_steel_station_roof_of_Zaandam_as_a_space_truss_construction_to_give_maximum_transparancy_to_the_townhall_-_panoramio.jpg/1280px-Modern_steel_station_roof_of_Zaandam_as_a_space_truss_construction_to_give_maximum_transparancy_to_the_townhall_-_panoramio.jpg",
        "licencia": "CC BY 3.0",
        "fuente": "Wikimedia Commons",
    },
    "portales_estructura": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/b0/Steel_Fabrication_Shop_Columns_and_Beams._Bar-Joist_Roof_Trusses_on_Ground_in_Foreground%2C_9-6-68_%2816843105081%29.jpg/1280px-Steel_Fabrication_Shop_Columns_and_Beams._Bar-Joist_Roof_Trusses_on_Ground_in_Foreground%2C_9-6-68_%2816843105081%29.jpg",
        "licencia": "Sin restricciones",
        "fuente": "Wikimedia Commons",
    },
    "malla_cerramiento": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/5/55/Chain-link_fence_2011.jpg",
        "licencia": "CC BY-SA 3.0",
        "fuente": "Wikimedia Commons",
    },
    "postes_cercamiento": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/0/09/Metal_Fence_Post%2C_Stemster_Hill_-_geograph.org.uk_-_7071871.jpg",
        "licencia": "CC BY-SA 2.0",
        "fuente": "Wikimedia Commons",
    },
    "luminaria_led": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/Floodlight_at_M._A._Chidambaram_Stadium%2C_Chennai.jpg/1280px-Floodlight_at_M._A._Chidambaram_Stadium%2C_Chennai.jpg",
        "licencia": "CC BY-SA 3.0",
        "fuente": "Wikimedia Commons",
    },
    "demarcacion": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/46/Jacob_Riis_Park_td_%282019-06-04%29_028_-_Basketball_Courts.jpg/1280px-Jacob_Riis_Park_td_%282019-06-04%29_028_-_Basketball_Courts.jpg",
        "licencia": "CC BY-SA 4.0",
        "fuente": "Wikimedia Commons",
    },
    "tablero_basquetbol": {
        "url": "https://upload.wikimedia.org/wikipedia/commons/d/db/Basketball_Hoop%2C_Birkenshaw_Bottoms_-_geograph.org.uk_-_5114502.jpg",
        "licencia": "CC BY-SA 2.0",
        "fuente": "Wikimedia Commons",
    },
}

PROYECTOS = [
    {
        "nombre": "Polideportivo Municipal de Guayaquil",
        "ubicacion": "Guayaquil, Guayas",
        "superficie": "1.800 m2 techados · 2 canchas",
        "anio": "2025",
        "estado": "Entregado",
        "descripcion": "Recuperación de dos canchas techadas en el sector urbano, con piso de goma, iluminación LED y nuevo cerramiento perimetral.",
        "inversion": "$268.000",
        "imagen": "https://images.unsplash.com/photo-1461896836934-ffe607ba8211?auto=format&fit=crop&w=1000&q=75",
    },
    {
        "nombre": "Complejo Deportivo Los Samanes",
        "ubicacion": "Guayaquil, Guayas",
        "superficie": "2.400 m2 · multicancha techada",
        "anio": "2024",
        "estado": "Entregado",
        "descripcion": "Obra nueva con cubierta metálica, pórticos de acero y losas de hormigón, más instalación deportiva completa para campeonato provincial.",
        "inversion": "$392.000",
        "imagen": "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1000&q=75",
    },
    {
        "nombre": "Centro Deportivo La Carolina",
        "ubicacion": "Quito, Pichincha",
        "superficie": "4.800 m2 · 3 canchas",
        "anio": "2024",
        "estado": "Entregado",
        "descripcion": "Plan maestro con tres canchas techadas, sistema de iluminación LED y espacios de apoyo para los eventos deportivos de la capital.",
        "inversion": "$735.000",
        "imagen": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?auto=format&fit=crop&w=1000&q=75",
    },
    {
        "nombre": "Gimnasio Municipal de Cuenca",
        "ubicacion": "Cuenca, Azuay",
        "superficie": "960 m2 techados",
        "anio": "2023",
        "estado": "Entregado",
        "descripcion": "Habilitación de piso deportivo de alta resistencia y cubierta a 12 m con aislación térmica, lista para competencias de altura.",
        "inversion": "$186.500",
        "imagen": "https://images.unsplash.com/photo-1431324155629-1a6deb1dec8d?auto=format&fit=crop&w=1000&q=75",
    },
    {
        "nombre": "Complejo Deportivo Ciudad de Manta",
        "ubicacion": "Manta, Manabí",
        "superficie": "2.100 m2 · multicancha",
        "anio": "2023",
        "estado": "Entregado",
        "descripcion": "Ejecución de losas de hormigón, cerramiento de malla y sistema de iluminación perimetral en zona costera con alta humedad.",
        "inversion": "$214.800",
        "imagen": "https://images.unsplash.com/photo-1546519638-68e109498ffc?auto=format&fit=crop&w=1000&q=75",
    },
    {
        "nombre": "Polideportivo Provincial de Portoviejo",
        "ubicacion": "Portoviejo, Manabí",
        "superficie": "2.850 m2 · 2 canchas",
        "anio": "2022",
        "estado": "Entregado",
        "descripcion": "Recuperación techada con estructura metálica nueva, piso asfáltico deportivo y demarcación reglamentaria para el torneo provincial.",
        "inversion": "$341.000",
        "imagen": "https://images.unsplash.com/photo-1519861531473-9200262188bf?auto=format&fit=crop&w=1000&q=75",
    },
]

SERVICIOS = [
    {
        "titulo": "Estudio de factibilidad",
        "texto": "Levantamiento en sitio, análisis de suelos y propuesta de programa preliminar para validar su proyecto en el territorio.",
    },
    {
        "titulo": "Proyecto e ingeniería",
        "texto": "Planos, detalles constructivos, cálculo estructural y coordinación de todas las especialidades.",
    },
    {
        "titulo": "Construcción y montaje",
        "texto": "Ejecución de obra, instalación de equipos deportivos y puesta en marcha de la instalación.",
    },
    {
        "titulo": "Mantención y soporte",
        "texto": "Plan anual de conservación de pisos, cubiertas e iluminación para prolongar la vida útil del recinto.",
    },
]


@main_bp.route("/")
def index():
    return render_template(
        "index.html",
        proyectos=PROYECTOS,
        servicios=SERVICIOS,
        imagenes=IMAGENES,
        total_materiales=Material.query.count(),
    )


@main_bp.route("/materiales")
def materiales():
    categorias = [
        fila[0]
        for fila in Material.query.with_entities(Material.categoria)
        .distinct()
        .order_by(Material.categoria.asc())
        .all()
    ]

    seleccion = (request.args.get("categoria") or "").strip()
    categoria_actual = "Todas"
    consulta = Material.query.order_by(Material.categoria.asc(), Material.nombre.asc())

    if seleccion and seleccion in categorias:
        categoria_actual = seleccion
        consulta = consulta.filter(Material.categoria == seleccion)

    items = []
    for material in consulta.all():
        imagen = IMAGENES_MATERIALES.get(material.clave, {})
        items.append(
            {
                "id": material.id,
                "clave": material.clave,
                "nombre": material.nombre,
                "unidad": material.unidad,
                "categoria": material.categoria,
                "precio_referencial": material.precio_referencial,
                "precio_con_merma": material.precio_con_merma,
                "merma_pct": material.merma_pct,
                "descripcion": material.descripcion,
                "imagen": imagen.get("url", ""),
                "licencia": imagen.get("licencia", ""),
                "fuente": imagen.get("fuente", ""),
            }
        )

    return render_template(
        "materiales.html",
        materiales=items,
        categorias=categorias,
        categoria_actual=categoria_actual,
        seleccion=seleccion,
    )
