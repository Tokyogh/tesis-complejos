from datetime import date, datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from . import db

ROLES = ("admin", "usuario")

ESTADOS_SOLICITUD = ("Pendiente", "En revisión", "Aprobado", "Rechazado")


def _ahora():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class User(UserMixin, db.Model):
    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False)
    correo = db.Column(db.String(180), nullable=False, unique=True, index=True)
    clave_hash = db.Column(db.String(255), nullable=False)
    organizacion = db.Column(db.String(120), nullable=True)
    telefono = db.Column(db.String(40), nullable=True)
    rol = db.Column(db.String(20), nullable=False, default="usuario", index=True)
    activo = db.Column(db.Boolean, nullable=False, default=True)
    creado_en = db.Column(db.DateTime, nullable=False, default=_ahora)
    ultimo_acceso = db.Column(db.DateTime, nullable=True)

    cotizaciones = db.relationship(
        "Cotizacion", back_populates="user", lazy="select", cascade="all, delete-orphan"
    )
    citas = db.relationship("Cita", back_populates="user", lazy="select", cascade="all, delete-orphan")

    __table_args__ = (db.CheckConstraint("rol IN ('admin', 'usuario')", name="ck_usuario_rol"),)

    @property
    def is_active(self):
        """Flask-Login no debe aceptar sesiones de cuentas desactivadas."""
        return bool(self.activo)

    def __repr__(self):
        return f"<User {self.correo} ({self.rol})>"

    @property
    def role(self):
        return self.rol

    @role.setter
    def role(self, valor):
        self.rol = valor if valor in ROLES else "usuario"

    @property
    def es_admin(self):
        return self.rol == "admin"

    @property
    def iniciales(self):
        partes = [p for p in (self.nombre or "").replace(",", " ").split() if p]
        if not partes:
            return "US"
        if len(partes) == 1:
            return partes[0][:2].upper()
        return (partes[0][0] + partes[-1][0]).upper()

    def set_password(self, clave):
        self.clave_hash = generate_password_hash(clave)

    def check_password(self, clave):
        if not self.clave_hash:
            return False
        return check_password_hash(self.clave_hash, clave or "")

    def registrar_acceso(self):
        self.ultimo_acceso = _ahora()


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
    estado = db.Column(db.String(30), nullable=False, default="Pendiente", index=True)
    observaciones = db.Column(db.Text, nullable=False, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True, index=True)
    creada_en = db.Column(db.DateTime, nullable=False, default=_ahora)

    user = db.relationship("User", back_populates="cotizaciones")

    __table_args__ = (db.CheckConstraint("estado != ''", name="ck_cotizacion_estado"),)

    def __repr__(self):
        return f"<Cotizacion #{self.id} {self.proyecto} {self.costo_total:.0f}>"

    @property
    def es_pendiente(self):
        return self.estado == "Pendiente"


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
    estado = db.Column(db.String(30), nullable=False, default="Pendiente", index=True)
    observaciones = db.Column(db.Text, nullable=False, default="")
    user_id = db.Column(db.Integer, db.ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=True, index=True)
    creada_en = db.Column(db.DateTime, nullable=False, default=_ahora)

    user = db.relationship("User", back_populates="citas")

    __table_args__ = (db.CheckConstraint("estado != ''", name="ck_cita_estado"),)

    def __repr__(self):
        return f"<Cita #{self.id} {self.nombre} {self.fecha}>"

    @property
    def es_pendiente(self):
        return self.estado == "Pendiente"

    @property
    def resuelta(self):
        return self.estado in ("Aprobado", "Rechazado")
