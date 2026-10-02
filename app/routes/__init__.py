from .admin_routes import admin_bp
from .auth_routes import auth_bp
from .calc_routes import calc_bp
from .contact_routes import contact_bp
from .main_routes import main_bp
from .panel_routes import panel_bp

__all__ = ["main_bp", "calc_bp", "contact_bp", "auth_bp", "admin_bp", "panel_bp", "register_blueprints"]


def register_blueprints(app):
    app.register_blueprint(main_bp)
    app.register_blueprint(calc_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(panel_bp)
    app.register_blueprint(admin_bp)
