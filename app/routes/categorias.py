from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.services import categoria_service
from app.services.categoria_service import CategoriaServiceError

categorias_bp = Blueprint("categorias", __name__, url_prefix="/categorias")


@categorias_bp.route("/")
@login_required
def index():
    busqueda = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = categoria_service.listar(busqueda, page, per_page)
    return render_template(
        "categorias/index.html",
        categorias=paginacion.items,
        paginacion=paginacion,
        busqueda=busqueda,
        opciones_padre=categoria_service.obtener_opciones_padre(),
    )


@categorias_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    try:
        categoria_service.crear(
            nombre=request.form.get("nombre", ""),
            descripcion=request.form.get("descripcion", ""),
            categoria_padre_id=request.form.get("categoria_padre_id", type=int),
        )
        return jsonify({"ok": True, "mensaje": "Categoría creada correctamente."})
    except CategoriaServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@categorias_bp.route("/<int:categoria_id>/editar", methods=["POST"])
@login_required
def editar(categoria_id):
    try:
        categoria_service.actualizar(
            categoria_id=categoria_id,
            nombre=request.form.get("nombre", ""),
            descripcion=request.form.get("descripcion", ""),
            categoria_padre_id=request.form.get("categoria_padre_id", type=int),
            activo=request.form.get("activo") == "on",
        )
        return jsonify({"ok": True, "mensaje": "Categoría actualizada correctamente."})
    except CategoriaServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@categorias_bp.route("/<int:categoria_id>/eliminar", methods=["POST"])
@login_required
def eliminar(categoria_id):
    try:
        categoria_service.eliminar(categoria_id)
        return jsonify({"ok": True, "mensaje": "Categoría eliminada correctamente."})
    except CategoriaServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
