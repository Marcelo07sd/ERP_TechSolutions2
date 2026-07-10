from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.services import rol_service
from app.services.rol_service import RolServiceError
from app.decorators import admin_required

roles_bp = Blueprint("roles", __name__, url_prefix="/roles")


@roles_bp.route("/")
@login_required
@admin_required
def index():
    busqueda = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = rol_service.listar(busqueda, page, per_page)
    return render_template(
        "roles/index.html",
        roles=paginacion.items,
        paginacion=paginacion,
        busqueda=busqueda,
    )


@roles_bp.route("/crear", methods=["POST"])
@login_required
@admin_required
def crear():
    try:
        rol_service.crear(
            nombre=request.form.get("nombre", ""),
            descripcion=request.form.get("descripcion", ""),
        )
        return jsonify({"ok": True, "mensaje": "Rol creado correctamente."})
    except RolServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@roles_bp.route("/<int:rol_id>/editar", methods=["POST"])
@login_required
@admin_required
def editar(rol_id):
    try:
        rol_service.actualizar(
            rol_id=rol_id,
            nombre=request.form.get("nombre", ""),
            descripcion=request.form.get("descripcion", ""),
        )
        return jsonify({"ok": True, "mensaje": "Rol actualizado correctamente."})
    except RolServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@roles_bp.route("/<int:rol_id>/eliminar", methods=["POST"])
@login_required
@admin_required
def eliminar(rol_id):
    try:
        rol_service.eliminar(rol_id)
        return jsonify({"ok": True, "mensaje": "Rol eliminado correctamente."})
    except RolServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
