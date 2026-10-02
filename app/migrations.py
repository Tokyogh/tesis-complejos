from sqlalchemy import inspect, text

from . import db

COLUMNAS_NUEVAS = {
    "cotizaciones": [
        ("estado", "VARCHAR(30) NOT NULL DEFAULT 'Pendiente'"),
        ("observaciones", "TEXT NOT NULL DEFAULT ''"),
        ("user_id", "INTEGER"),
    ],
    "citas": [
        ("estado", "VARCHAR(30) NOT NULL DEFAULT 'Pendiente'"),
        ("observaciones", "TEXT NOT NULL DEFAULT ''"),
        ("user_id", "INTEGER"),
    ],
}

INDICES = [
    "CREATE INDEX IF NOT EXISTS ix_cotizaciones_estado ON cotizaciones (estado)",
    "CREATE INDEX IF NOT EXISTS ix_citas_estado ON citas (estado)",
    "CREATE INDEX IF NOT EXISTS ix_cotizaciones_user_id ON cotizaciones (user_id)",
    "CREATE INDEX IF NOT EXISTS ix_citas_user_id ON citas (user_id)",
]


def aplicar_migraciones():
    """Agrega a las tablas ya existentes las columnas del esquema de autenticación."""
    inspector = inspect(db.engine)
    existentes = set(inspector.get_table_names())
    aplicadas = []

    for tabla, columnas in COLUMNAS_NUEVAS.items():
        if tabla not in existentes:
            continue
        actuales = {columna["name"] for columna in inspector.get_columns(tabla)}
        for nombre, definicion in columnas:
            if nombre in actuales:
                continue
            with db.engine.begin() as conexion:
                conexion.execute(text(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {definicion}"))
            aplicadas.append(f"{tabla}.{nombre}")

    if aplicadas:
        with db.engine.begin() as conexion:
            for sentencia in INDICES:
                conexion.execute(text(sentencia))

    return aplicadas
