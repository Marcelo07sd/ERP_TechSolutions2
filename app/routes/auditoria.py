from flask import Blueprint, render_template, request, current_app
from flask_login import login_required

from app.models.usuario import Usuario
from app.services import auditoria_service

auditoria_bp = Blueprint("auditoria", __name__, url_prefix="/auditoria")


@auditoria_bp.route("/")
@login_required
def index():
    tabla = request.args.get("tabla") or None
    accion = request.args.get("accion") or None
    usuario_id = request.args.get("usuario_id", type=int)
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = auditoria_service.listar(tabla, accion, usuario_id, page, per_page)
    return render_template(
        "auditoria/index.html",
        registros=paginacion.items, paginacion=paginacion,
        tabla=tabla, accion=accion, usuario_id=usuario_id,
        tablas_disponibles=auditoria_service.tablas_disponibles(),
        usuarios=Usuario.query.order_by(Usuario.nombre).all(),
    )
