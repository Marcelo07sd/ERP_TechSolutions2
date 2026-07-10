from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.services import pedido_service
from app.services.pedido_service import PedidoServiceError

pedidos_bp = Blueprint("pedidos", __name__, url_prefix="/pedidos")


@pedidos_bp.route("/")
@login_required
def index():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado") or None
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = pedido_service.listar(busqueda, estado, page, per_page)
    return render_template(
        "pedidos/index.html", pedidos=paginacion.items, paginacion=paginacion, busqueda=busqueda, estado=estado
    )


@pedidos_bp.route("/<int:pedido_id>")
@login_required
def detalle(pedido_id):
    pedido = pedido_service.obtener(pedido_id)
    pasos = ["procesando", "en_camino", "entregado"]
    indice_estado = pasos.index(pedido.estado.value) if pedido.estado.value in pasos else -1
    return render_template("pedidos/detalle.html", pedido=pedido, pasos=pasos, indice_estado=indice_estado)


@pedidos_bp.route("/<int:pedido_id>/cambiar-estado", methods=["POST"])
@login_required
def cambiar_estado(pedido_id):
    try:
        pedido_service.cambiar_estado(
            pedido_id,
            nuevo_estado=request.form.get("estado"),
            transportista=request.form.get("transportista"),
            numero_seguimiento=request.form.get("numero_seguimiento"),
        )
        return jsonify({"ok": True, "mensaje": "Estado del pedido actualizado correctamente."})
    except PedidoServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
