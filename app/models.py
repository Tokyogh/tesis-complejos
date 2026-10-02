from datetime import date, datetime, timezone

from . import db


class Material(db.Model):
    __tablename__ = "materiales"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    clave = db.Column(db.String(60), nullable=False, unique=True, index=True)
    unidad = db.Column(db.String(30), nullable=False)
    categoria = db.Column(db.String(60), nullable=False, index=True)
    precio_referencial = db.Column(db.Float, nullable=False, default=0.0)
    merma_pct = db.Column(db.Float, nullable=False, default=5.0)
    descripcion = db.Column(db.Text, nullable=False, default="")

    __table_args__ = (db.CheckConstraint("precio_referencial >= 0", name="ck_material_precio_positivo"),)

    def __repr__(self):
        return f"<Material {self.nombre} ({self.unidad})>"

    @property
    def precio_con_merma(self):
        return round(self.precio_referencial * (1 + (self.merma_pct or 0) / 100), 2)


class Cotizacion(db.Model):
    __tablename__ = "cotizaciones"

    id = db.Column(db.Integer, primary_key=True)
    proyecto = db.Column(db.String(150), nullable=False)
    solicitante = db.Column(db.String(120), nullable=True)
    correo = db.Column(db.String(180), nullable=True)
    largo = db.Column(db.Float, nullable=False)
    ancho = db.Column(db.Float, nullable=False)
    altura = db.Column(db.Float, nullable=False)
    num_canchas = db.Column(db.Integer, nullable=False, default=1)
    superficie = db.Column(db.Float, nullable=False)
    costo_directo = db.Column(db.Float, nullable=False)
    costo_total = db.Column(db.Float, nullable=False)
    detalle_json = db.Column(db.Text, nullable=False, default="[]")
    creada_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Cotizacion #{self.id} {self.proyecto} {self.costo_total:.0f}>"


class Cita(db.Model):
    __tablename__ = "citas"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(180), nullable=False)
    telefono = db.Column(db.String(40), nullable=True)
    fecha = db.Column(db.Date, nullable=False, default=date.today)
    tipo = db.Column(db.String(40), nullable=False, default="Visita a obra")
    mensaje = db.Column(db.Text, nullable=False, default="")
    atendida = db.Column(db.Boolean, nullable=False, default=False)
    creada_en = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Cita #{self.id} {self.nombre} {self.fecha}>"