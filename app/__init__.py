import os
from datetime import date, datetime
from pathlib import Path

import click
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "auth.login"
login_manager.login_message = "Inicia sesión para acceder a esa sección."
login_manager.login_message_category = "aviso"
login_manager.session_protection = "strong"

BASE_DIR = Path(__file__).resolve().parent.parent

ESTILOS_ESTADO = {
    "Pendiente": "estado-pendiente",
    "En revisión": "estado-revision",
    "Aprobado": "estado-aprobado",
    "Rechazado": "estado-rechazado",
}


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "sistema-polideportivo-clave-de-desarrollo"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{Path(app.instance_path) / 'database.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_DURATION=60 * 60 * 24 * 14,
        CSRF_ENABLED=True,
        AUTO_CREATE_DB=True,
        AUTO_SEED=True,
    )

    if test_config:
        app.config.update(test_config)
    # Las pruebas usan clientes Flask sin gestión explícita de tokens CSRF.
    # Mantener la protección activa por defecto en cualquier ejecución normal.
    if app.testing and "CSRF_ENABLED" not in (test_config or {}):
        app.config["CSRF_ENABLED"] = False

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)
    login_manager.init_app(app)

    from .csrf import csrf_token, proteger_csrf

    app.before_request(proteger_csrf)
    app.jinja_env.globals["csrf_token"] = csrf_token

    from . import models  # noqa: F401

    from .routes import register_blueprints

    register_blueprints(app)
    register_template_helpers(app)
    register_cli(app)
    register_error_handlers(app)
    register_login()

    if app.config.get("AUTO_CREATE_DB"):
        with app.app_context():
            db.create_all()
            from .migrations import aplicar_migraciones

            aplicadas = aplicar_migraciones()
            if aplicadas and not app.config.get("TESTING"):
                app.logger.info("Migracion aplicada: %s", ", ".join(aplicadas))
        if app.config.get("AUTO_SEED"):
            from .seed import seed_materiales

            with app.app_context():
                seed_materiales()

    return app


def register_login():
    from .models import User

    @login_manager.user_loader
    def cargar_usuario(identificador):
        try:
            return db.session.get(User, int(identificador))
        except (TypeError, ValueError):
            return None

    @login_manager.unauthorized_handler
    def no_autorizado():
        from flask import redirect, request, url_for

        return redirect(url_for("auth.login", next=request.full_path))


def register_template_helpers(app):
    @app.context_processor
    def inject_contextos():
        from .models import ESTADOS_SOLICITUD

        return {
            "anio_actual": datetime.now().year,
            "estados_solicitud": ESTADOS_SOLICITUD,
            "estilos_estado": ESTILOS_ESTADO,
        }

    @app.template_filter("usd")
    def format_usd(value):
        try:
            amount = float(value or 0)
        except (TypeError, ValueError):
            amount = 0.0
        return f"${amount:,.2f}"

    @app.template_filter("num")
    def format_num(value, decimales=2):
        try:
            number = float(value or 0)
        except (TypeError, ValueError):
            number = 0.0
        if number <= 0:
            return 0 if int(decimales) == 0 else number
        if int(decimales) == 0:
            return int(round(number))
        return round(number, int(decimales))

    @app.template_filter("fecha")
    def format_fecha(value):
        if isinstance(value, datetime):
            return value.strftime("%d/%m/%Y %H:%M")
        if isinstance(value, date):
            return value.strftime("%d/%m/%Y")
        return ""


def register_cli(app):
    @app.cli.command("init-db")
    def init_db():
        """Crea todas las tablas del esquema en SQLite."""
        db.create_all()
        from .migrations import aplicar_migraciones

        aplicadas = aplicar_migraciones()
        click.echo(f"Tablas creadas correctamente. Migraciones: {len(aplicadas)} columna(s) agregada(s).")

    @app.cli.command("seed")
    def seed_command():
        """Puebla la base de datos con el catalogo referencial de materiales."""
        from .seed import seed_materiales

        insertados = seed_materiales(forzar=True)
        click.echo(f"Seed completado: {insertados} materiales sincronizados.")

    @app.cli.command("crear-admin")
    @click.option("--nombre", prompt="Nombre y apellido")
    @click.option("--correo", prompt="Correo electronico")
    @click.option("--clave", prompt=True, hide_input=True, confirmation_prompt=True)
    def crear_admin(nombre, correo, clave):
        """Crea (o actualiza) una cuenta de administrador."""
        from .models import User

        correo = correo.strip().lower()
        usuario = User.query.filter_by(correo=correo).first()
        creado = usuario is None

        if usuario is None:
            usuario = User(nombre=nombre.strip(), correo=correo, rol="admin")
            db.session.add(usuario)
        else:
            usuario.nombre = nombre.strip()
            usuario.rol = "admin"
            usuario.activo = True

        usuario.set_password(clave)
        db.session.commit()
        accion = "creada" if creado else "actualizada"
        click.echo(f"Cuenta de administracion {accion}: {usuario.correo}")


def register_error_handlers(app):
    @app.errorhandler(400)
    def bad_request(_error):
        from flask import render_template

        return render_template("400.html", codigo=400), 400

    @app.errorhandler(403)
    def forbidden(_error):
        from flask import render_template

        return render_template("403.html", codigo=403), 403

    @app.errorhandler(404)
    def not_found(_error):
        from flask import render_template

        return render_template("404.html", codigo=404), 404

    @app.errorhandler(500)
    def server_error(_error):
        from flask import render_template

        return render_template("500.html", codigo=500), 500
