from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.models.producto import Producto
from app.services import inventario_service
from app.services.inventario_service import InventarioServiceError

inventario_bp = Blueprint("inventario", __name__, url_prefix="/inventario")


@inventario_bp.route("/")
@login_required
def index():
    producto_id = request.args.get("producto_id", type=int)
    tipo = request.args.get("tipo") or None
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = inventario_service.listar_movimientos(producto_id, tipo, page, per_page)
    return render_template(
        "inventario/index.html",
        movimientos=paginacion.items,
        paginacion=paginacion,
        productos=Producto.query.filter_by(activo=True).order_by(Producto.nombre).all(),
        producto_id=producto_id,
        tipo=tipo,
        productos_stock_bajo=inventario_service.productos_stock_bajo(),
    )


@inventario_bp.route("/entrada", methods=["POST"])
@login_required
def entrada():
    try:
        inventario_service.registrar_entrada(
            producto_id=request.form.get("producto_id", type=int),
            cantidad=request.form.get("cantidad", type=int),
            motivo=request.form.get("motivo", "Entrada manual"),
        )
        return jsonify({"ok": True, "mensaje": "Entrada registrada correctamente."})
    except InventarioServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@inventario_bp.route("/salida", methods=["POST"])
@login_required
def salida():
    try:
        inventario_service.registrar_salida(
            producto_id=request.form.get("producto_id", type=int),
            cantidad=request.form.get("cantidad", type=int),
            motivo=request.form.get("motivo", "Salida manual"),
        )
        return jsonify({"ok": True, "mensaje": "Salida registrada correctamente."})
    except InventarioServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@inventario_bp.route("/ajuste", methods=["POST"])
@login_required
def ajuste():
    try:
        inventario_service.registrar_ajuste(
            producto_id=request.form.get("producto_id", type=int),
            nuevo_stock=request.form.get("nuevo_stock", type=int),
            motivo=request.form.get("motivo", "Ajuste manual"),
        )
        return jsonify({"ok": True, "mensaje": "Ajuste registrado correctamente."})
    except InventarioServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
