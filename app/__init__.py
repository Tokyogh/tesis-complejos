import os
from datetime import date, datetime
from pathlib import Path

import click
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

BASE_DIR = Path(__file__).resolve().parent.parent


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", "sistema-polideportivo-clave-de-desarrollo"),
        SQLALCHEMY_DATABASE_URI=os.environ.get(
            "DATABASE_URL", f"sqlite:///{Path(app.instance_path) / 'database.db'}"
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SQLALCHEMY_ENGINE_OPTIONS={"pool_pre_ping": True},
        AUTO_CREATE_DB=True,
        AUTO_SEED=True,
    )

    if test_config:
        app.config.update(test_config)

    os.makedirs(app.instance_path, exist_ok=True)

    db.init_app(app)

    from . import models  # noqa: F401

    from .routes import register_blueprints

    register_blueprints(app)
    register_template_helpers(app)
    register_cli(app)
    register_error_handlers(app)

    if app.config.get("AUTO_CREATE_DB"):
        with app.app_context():
            db.create_all()
        if app.config.get("AUTO_SEED"):
            from .seed import seed_materiales

            with app.app_context():
                seed_materiales()

    return app


def register_blueprints(app):
    from .routes.main_routes import main_bp
    from .routes.calc_routes import calc_bp
    from .routes.contact_routes import contact_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(calc_bp)
    app.register_blueprint(contact_bp)


def register_template_helpers(app):
    @app.context_processor
    def inject_contextos():
        return {"anio_actual": datetime.now().year}

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
        click.echo("Tablas creadas correctamente.")

    @app.cli.command("seed")
    def seed_command():
        """Puebla la base de datos con el catalogo referencial de materiales."""
        from .seed import seed_materiales

        insertados = seed_materiales(forzar=True)
        click.echo(f"Seed completado: {insertados} materiales sincronizados.")


def register_error_handlers(app):
    @app.errorhandler(404)
    def not_found(_error):
        from flask import render_template

        return render_template("404.html", codigo=404), 404

    @app.errorhandler(500)
    def server_error(_error):
        from flask import render_template

        return render_template("500.html", codigo=500), 500