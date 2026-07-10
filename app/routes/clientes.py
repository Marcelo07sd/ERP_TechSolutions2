from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.services import cliente_service
from app.services.cliente_service import ClienteServiceError

clientes_bp = Blueprint("clientes", __name__, url_prefix="/clientes")


@clientes_bp.route("/")
@login_required
def index():
    busqueda = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = cliente_service.listar(busqueda, page, per_page)
    return render_template(
        "clientes/index.html", clientes=paginacion.items, paginacion=paginacion, busqueda=busqueda
    )


@clientes_bp.route("/nuevo")
@login_required
def nuevo():
    return render_template("clientes/form.html", cliente=None)


@clientes_bp.route("/<int:cliente_id>/editar")
@login_required
def editar(cliente_id):
    cliente = cliente_service.obtener(cliente_id)
    return render_template("clientes/form.html", cliente=cliente)


@clientes_bp.route("/guardar", methods=["POST"])
@clientes_bp.route("/<int:cliente_id>/guardar", methods=["POST"])
@login_required
def guardar(cliente_id=None):
    datos = request.form.to_dict()
    try:
        if cliente_id:
            cliente_service.actualizar(cliente_id, datos)
        else:
            cliente_service.crear(datos)
        return jsonify({"ok": True, "mensaje": "Cliente guardado correctamente.", "redirect": "/clientes/"})
    except ClienteServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@clientes_bp.route("/<int:cliente_id>")
@login_required
def detalle(cliente_id):
    from app.models.venta import Venta
    cliente = cliente_service.obtener(cliente_id)
    ventas_recientes = (
        cliente.ventas.order_by(Venta.fecha_venta.desc()).limit(10).all()
    )
    tickets_recientes = cliente.tickets_soporte.limit(10).all()
    return render_template(
        "clientes/detalle.html", cliente=cliente,
        ventas_recientes=ventas_recientes, tickets_recientes=tickets_recientes,
    )


@clientes_bp.route("/<int:cliente_id>/eliminar", methods=["POST"])
@login_required
def eliminar(cliente_id):
    try:
        cliente_service.eliminar(cliente_id)
        return jsonify({"ok": True, "mensaje": "Cliente eliminado correctamente."})
    except ClienteServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
