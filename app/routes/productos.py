from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.models.categoria import Categoria
from app.services import producto_service
from app.services.producto_service import ProductoServiceError

productos_bp = Blueprint("productos", __name__, url_prefix="/productos")


@productos_bp.route("/")
@login_required
def index():
    busqueda = request.args.get("q", "").strip()
    categoria_id = request.args.get("categoria_id", type=int)
    solo_stock_bajo = request.args.get("stock_bajo") == "1"
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = producto_service.listar(busqueda, categoria_id, solo_stock_bajo, page, per_page)
    return render_template(
        "productos/index.html",
        productos=paginacion.items,
        paginacion=paginacion,
        busqueda=busqueda,
        categoria_id=categoria_id,
        solo_stock_bajo=solo_stock_bajo,
        categorias=Categoria.query.order_by(Categoria.nombre).all(),
    )


@productos_bp.route("/nuevo")
@login_required
def nuevo():
    return render_template("productos/form.html", producto=None, categorias=Categoria.query.order_by(Categoria.nombre).all())


@productos_bp.route("/<int:producto_id>/editar")
@login_required
def editar(producto_id):
    from app.models.producto import Producto
    producto = Producto.query.get_or_404(producto_id)
    return render_template("productos/form.html", producto=producto, categorias=Categoria.query.order_by(Categoria.nombre).all())


@productos_bp.route("/guardar", methods=["POST"])
@productos_bp.route("/<int:producto_id>/guardar", methods=["POST"])
@login_required
def guardar(producto_id=None):
    datos = request.form.to_dict()
    try:
        if producto_id:
            producto_service.actualizar(producto_id, datos)
        else:
            producto_service.crear(datos)
        return jsonify({"ok": True, "mensaje": "Producto guardado correctamente.", "redirect": "/productos/"})
    except ProductoServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@productos_bp.route("/<int:producto_id>/eliminar", methods=["POST"])
@login_required
def eliminar(producto_id):
    try:
        producto_service.eliminar(producto_id)
        return jsonify({"ok": True, "mensaje": "Producto eliminado correctamente."})
    except ProductoServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
