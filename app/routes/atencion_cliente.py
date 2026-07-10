from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import login_required

from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.services import ticket_service
from app.services.ticket_service import TicketServiceError

atencion_bp = Blueprint("atencion", __name__, url_prefix="/atencion-cliente")


@atencion_bp.route("/")
@login_required
def index():
    busqueda = request.args.get("q", "").strip()
    estado = request.args.get("estado") or None
    prioridad = request.args.get("prioridad") or None
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["ITEMS_PER_PAGE"]

    paginacion = ticket_service.listar(busqueda, estado, prioridad, page, per_page)
    return render_template(
        "atencion_cliente/index.html",
        tickets=paginacion.items, paginacion=paginacion,
        busqueda=busqueda, estado=estado, prioridad=prioridad,
    )


@atencion_bp.route("/nuevo")
@login_required
def nuevo():
    return render_template(
        "atencion_cliente/form.html",
        clientes=Cliente.query.filter_by(activo=True).order_by(Cliente.nombre).all(),
        agentes=Usuario.query.filter_by(activo=True).order_by(Usuario.nombre).all(),
    )


@atencion_bp.route("/crear", methods=["POST"])
@login_required
def crear():
    try:
        ticket = ticket_service.crear(request.form.to_dict())
        return jsonify({"ok": True, "mensaje": f"Ticket {ticket.codigo} creado correctamente.", "redirect": f"/atencion-cliente/{ticket.id}"})
    except TicketServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@atencion_bp.route("/<int:ticket_id>")
@login_required
def detalle(ticket_id):
    ticket = ticket_service.obtener(ticket_id)
    return render_template("atencion_cliente/detalle.html", ticket=ticket)


@atencion_bp.route("/<int:ticket_id>/comentar", methods=["POST"])
@login_required
def comentar(ticket_id):
    try:
        ticket_service.agregar_comentario(ticket_id, request.form.get("mensaje", ""))
        return jsonify({"ok": True, "mensaje": "Comentario agregado correctamente."})
    except TicketServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400


@atencion_bp.route("/<int:ticket_id>/cambiar-estado", methods=["POST"])
@login_required
def cambiar_estado(ticket_id):
    try:
        ticket_service.cambiar_estado(ticket_id, request.form.get("estado"))
        return jsonify({"ok": True, "mensaje": "Estado del ticket actualizado correctamente."})
    except TicketServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
