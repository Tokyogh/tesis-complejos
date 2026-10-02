from .calc_routes import calc_bp
from .contact_routes import contact_bp
from .main_routes import main_bp

__all__ = ["main_bp", "calc_bp", "contact_bp", "register_blueprints"]


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(calc_bp)
    app.register_blueprint(contact_bp)