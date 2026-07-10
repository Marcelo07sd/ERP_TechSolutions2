from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.models.cliente import Cliente
from app.models.producto import Producto
from app.services import venta_service
from app.services.venta_service import VentaServiceError

ventas_bp = Blueprint("ventas", __name__, url_prefix="/ventas")


@ventas_bp.route("/")
@login_required
def index():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado") or None
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = venta_service.listar(busqueda, estado, page, per_page)
    return render_template(
        "ventas/index.html",
        ventas=paginacion.items,
        paginacion=paginacion,
        busqueda=busqueda,
        estado=estado,
    )


@ventas_bp.route("/nueva")
@login_required
def nueva():
    return render_template(
        "ventas/nueva.html",
        clientes=Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all(),
        productos=Producto.query.filter(Producto.activo.is_(True), Producto.stock_actual > 0).order_by(Producto.nombre).all(),
    )


@ventas_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    payload = request.get_json(silent=True) or {}
    try:
        venta = venta_service.crear_venta(
            cliente_id=payload.get("cliente_id"),
            metodo_pago=payload.get("metodo_pago"),
            lineas=payload.get("lineas", []),
            generar_pedido=payload.get("generar_pedido", True),
            direccion_envio=payload.get("direccion_envio"),
        )
        return jsonify({
            "ok": True,
            "mensaje": f"Venta {venta.numero_venta} registrada correctamente.",
            "redirect": f"/ventas/{venta.id}",
        })
    except VentaServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@ventas_bp.route("/<int:venta_id>")
@login_required
def detalle(venta_id):
    from app.models.venta import Venta
    venta = Venta.query.get_or_404(venta_id)
    return render_template("ventas/detalle.html", venta=venta)


@ventas_bp.route("/<int:venta_id>/anular", methods=["POST"])
@login_required
def anular(venta_id):
    try:
        venta_service.anular_venta(venta_id, request.form.get("motivo", "Sin motivo especificado"))
        return jsonify({"ok": True, "mensaje": "Venta anulada y stock repuesto correctamente."})
    except VentaServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
