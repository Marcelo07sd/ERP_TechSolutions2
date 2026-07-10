from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.services import usuario_service, rol_service
from app.services.usuario_service import UsuarioServiceError
from app.decorators import admin_required

usuarios_bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@usuarios_bp.route("/")
@login_required
@admin_required
def index():
    busqueda = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = usuario_service.listar(busqueda, page, per_page)
    roles = rol_service.obtener_todos()
    return render_template(
        "usuarios/index.html",
        usuarios=paginacion.items,
        paginacion=paginacion,
        busqueda=busqueda,
        roles=roles,
    )


@usuarios_bp.route("/nuevo")
@login_required
@admin_required
def nuevo():
    roles = rol_service.obtener_todos()
    return render_template("usuarios/form.html", usuario=None, roles=roles)


@usuarios_bp.route("/<int:usuario_id>/editar")
@login_required
@admin_required
def editar(usuario_id):
    usuario = usuario_service.obtener(usuario_id)
    roles = rol_service.obtener_todos()
    return render_template("usuarios/form.html", usuario=usuario, roles=roles)


@usuarios_bp.route("/guardar", methods=["POST"])
@usuarios_bp.route("/<int:usuario_id>/guardar", methods=["POST"])
@login_required
@admin_required
def guardar(usuario_id=None):
    datos = request.form.to_dict()
    try:
        if usuario_id:
            usuario_service.actualizar(usuario_id, datos)
        else:
            usuario_service.crear(datos)
        return jsonify({"ok": True, "mensaje": "Usuario guardado correctamente.", "redirect": "/usuarios/"})
    except UsuarioServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@usuarios_bp.route("/<int:usuario_id>/eliminar", methods=["POST"])
@login_required
@admin_required
def eliminar(usuario_id):
    try:
        usuario_service.eliminar(usuario_id)
        return jsonify({"ok": True, "mensaje": "Usuario eliminado correctamente."})
    except UsuarioServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
