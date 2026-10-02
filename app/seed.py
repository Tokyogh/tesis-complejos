from . import db
from .models import Material

MATERIALES_BASE = [
    {
        "clave": "terreno_compactacion",
        "nombre": "Desbroce, relleno y compactación de terreno",
        "unidad": "m3",
        "categoria": "Preliminares",
        "precio_referencial": 14.50,
        "merma_pct": 10.0,
        "descripcion": "Desbroce, relleno seleccionado y compactación con maquinaria media. Base de soporte para la losa, ajustada al tipo de suelo local.",
    },
    {
        "clave": "hormigon_premezclado",
        "nombre": "Hormigón premezclado H20",
        "unidad": "m3",
        "categoria": "Losas",
        "precio_referencial": 150.00,
        "merma_pct": 5.0,
        "descripcion": "Concreto de 20 MPa (H20) para losas y fundaciones, dosificado en planta y colocado en sitio. Incluye bombeo y curado.",
    },
    {
        "clave": "malla_losa",
        "nombre": "Malla acanalada C92 para refuerzo de losa",
        "unidad": "m2",
        "categoria": "Losas",
        "precio_referencial": 10.50,
        "merma_pct": 8.0,
        "descripcion": "Malla de acero electrosoldada para el refuerzo de la losa y el control de fisuras, con traslape de 10 cm entre paneles.",
    },
    {
        "clave": "piso_deportivo",
        "nombre": "Manta asfáltica sportiva 10 mm",
        "unidad": "m2",
        "categoria": "Pisos deportivos",
        "precio_referencial": 26.00,
        "merma_pct": 8.0,
        "descripcion": "Piso de goma polimérica con acabado en poliuretano, para áreas techadas de alto tráfico y clima de costa.",
    },
    {
        "clave": "cesped_sintetico",
        "nombre": "Césped sintético Figaro 50 mm",
        "unidad": "m2",
        "categoria": "Pisos deportivos",
        "precio_referencial": 42.00,
        "merma_pct": 10.0,
        "descripcion": "Césped sintético de fibra de 50 mm con relleno de caucho y sílice, con tratamiento UV para el clima ecuatorial.",
    },
    {
        "clave": "estructura_cubierta",
        "nombre": "Estructura metálica para cubierta galvanizada",
        "unidad": "m2",
        "categoria": "Estructura",
        "precio_referencial": 39.00,
        "merma_pct": 5.0,
        "descripcion": "Estructura de acero galvanizado en caliente (ASTM A36/A572), cerchas o arcos más placas de cobertura metálica.",
    },
    {
        "clave": "portales_estructura",
        "nombre": "Portal metálico prefabricado",
        "unidad": "unidad",
        "categoria": "Estructura",
        "precio_referencial": 300.00,
        "merma_pct": 0.0,
        "descripcion": "Portal de acero estructural con fundación y anclajes, dimensionado según la luz entre apoyos y la demanda sísmica (NEC-15).",
    },
    {
        "clave": "malla_cerramiento",
        "nombre": "Malla metálica para cerramiento",
        "unidad": "m2",
        "categoria": "Cerramiento",
        "precio_referencial": 17.00,
        "merma_pct": 8.0,
        "descripcion": "Malla electrosoldada 50x50x2 mm con revestimiento de polietileno anticorrosivo, para protección perimetral del recinto.",
    },
    {
        "clave": "postes_cercamiento",
        "nombre": "Poste de acero galvanizado 3\"",
        "unidad": "unidad",
        "categoria": "Cerramiento",
        "precio_referencial": 49.00,
        "merma_pct": 5.0,
        "descripcion": "Poste tubular galvanizado de 2,40 m con tapa superior y fundación de hormigón, según la altura del cerramiento.",
    },
    {
        "clave": "luminaria_led",
        "nombre": "Luminaria LED flood 200 W",
        "unidad": "unidad",
        "categoria": "Iluminación",
        "precio_referencial": 64.00,
        "merma_pct": 0.0,
        "descripcion": "Reflector LED IP65 con driver dimerizable, de 500 a 750 lux sobre el plano de juego según el nivel de competencia.",
    },
    {
        "clave": "demarcacion",
        "nombre": "Pintura acrílica de demarcación",
        "unidad": "litro",
        "categoria": "Pinturas",
        "precio_referencial": 11.00,
        "merma_pct": 10.0,
        "descripcion": "Pintura acrílica de alta adherencia para líneas, zonas de seguridad y demarcación reglamentaria de canchas.",
    },
    {
        "clave": "tablero_basquetbol",
        "nombre": "Tablero de básquetbol en fibra de vidrio",
        "unidad": "unidad",
        "categoria": "Equipamiento",
        "precio_referencial": 1560.00,
        "merma_pct": 0.0,
        "descripcion": "Tablero tipo FIBA con aro retráctil y vidrio templado, instalado a 3,05 m sobre el piso de juego.",
    },
]


def seed_materiales(forzar=False):
    """Inserta el catálogo referencial. Con `forzar` sincroniza también los precios existentes."""
    sincronizados = 0
    existentes = {material.clave: material for material in Material.query.all()}

    for datos in MATERIALES_BASE:
        material = existentes.get(datos["clave"])
        if material is None:
            db.session.add(Material(**datos))
            sincronizados += 1
        elif forzar:
            for campo, valor in datos.items():
                setattr(material, campo, valor)
            sincronizados += 1

    db.session.commit()
    return sincronizados