from flask import Flask, request, jsonify
from urllib.parse import urlencode

from app.config import get_config
from app.extensions import db, migrate, login_manager, csrf


def create_app():
    """Application Factory: permite crear múltiples instancias de la app
    (útil para testing) y evita imports circulares entre extensiones,
    modelos y blueprints."""

    app = Flask(__name__)
    app.config.from_object(get_config())

    # --- Extensiones ---
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    csrf.init_app(app)

    app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hora de expiración
    app.config["WTF_CSRF_SSL_STRICT"] = False  # compatible con HTTP local

    # Import de modelos DESPUÉS de db.init_app para que Alembic los detecte
    with app.app_context():
        from app import models  # noqa: F401

    from app.models.usuario import Usuario

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(Usuario, int(user_id))

    # --- Blueprints ---
    from app.routes.auth import auth_bp
    from app.routes.dashboard import dashboard_bp
    from app.routes.categorias import categorias_bp
    from app.routes.productos import productos_bp
    from app.routes.inventario import inventario_bp
    from app.routes.ventas import ventas_bp
    from app.routes.clientes import clientes_bp
    from app.routes.pedidos import pedidos_bp
    from app.routes.atencion_cliente import atencion_bp
    from app.routes.auditoria import auditoria_bp
    from app.routes.roles import roles_bp
    from app.routes.usuarios import usuarios_bp
    from app.routes.reportes import reportes_bp
    from app.routes.solicitudes import solicitudes_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(categorias_bp)
    app.register_blueprint(productos_bp)
    app.register_blueprint(inventario_bp)
    app.register_blueprint(ventas_bp)
    app.register_blueprint(clientes_bp)
    app.register_blueprint(pedidos_bp)
    app.register_blueprint(atencion_bp)
    app.register_blueprint(auditoria_bp)
    app.register_blueprint(roles_bp)
    app.register_blueprint(usuarios_bp)
    app.register_blueprint(reportes_bp)
    app.register_blueprint(solicitudes_bp)

    # --- Seguridad: cabeceras HTTP ---
    @app.after_request
    def add_security_headers(response):
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        return response

    # --- Filtros / helpers de Jinja disponibles en toda plantilla ---
    from app.time_utils import ahora, a_peru

    @app.context_processor
    def inject_globals():
        return {"anio_actual": ahora().year, "app_nombre": "TechSolutions Perú"}

    @app.template_filter("peru")
    def formato_peru(dt):
        if dt is None:
            return "—"
        return dt.strftime("%d/%m/%Y %H:%M")

    @app.template_filter("peru_fecha")
    def formato_peru_fecha(dt):
        if dt is None:
            return "—"
        return dt.strftime("%d/%m/%Y")

    @app.template_filter("peru_hora")
    def formato_peru_hora(dt):
        if dt is None:
            return "—"
        return dt.strftime("%H:%M")

    @app.template_filter("moneda")
    def formato_moneda(valor):
        try:
            return f"S/ {float(valor):,.2f}"
        except (TypeError, ValueError):
            return "S/ 0.00"

    @app.template_global("url_pagina")
    def url_pagina(pagina):
        """Devuelve la URL actual reemplazando solo el parámetro 'page',
        preservando el resto de filtros/búsqueda ya aplicados."""
        from flask import request
        args = request.args.to_dict()
        args["page"] = pagina
        return f"{request.path}?{urlencode(args)}"

    return app
