"""Lógica de negocio del módulo Atención al Cliente (tickets de soporte)."""

from flask_login import current_user
from app.time_utils import ahora
from sqlalchemy import func, cast, Integer

from app.extensions import db
from app.models.atencion_cliente import (
    TicketSoporte, ComentarioTicket, CategoriaTicket, PrioridadTicket, EstadoTicket
)
from app.models.cliente import Cliente
from app.services import auditoria_service


class TicketServiceError(Exception):
    pass


def listar(busqueda: str = "", estado: str | None = None, prioridad: str | None = None,
           page: int = 1, per_page: int = 10):
    query = TicketSoporte.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.join(Cliente).filter(
            db.or_(TicketSoporte.codigo.ilike(like), TicketSoporte.asunto.ilike(like), Cliente.nombre.ilike(like))
        )
    if estado:
        query = query.filter(TicketSoporte.estado == EstadoTicket(estado))
    if prioridad:
        query = query.filter(TicketSoporte.prioridad == PrioridadTicket(prioridad))
    query = query.order_by(TicketSoporte.fecha_creacion.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener(ticket_id: int) -> TicketSoporte:
    return TicketSoporte.query.get_or_404(ticket_id)


def _siguiente_codigo() -> str:
    maximo = db.session.query(
        func.max(cast(func.substr(TicketSoporte.codigo, 4), Integer))
    ).scalar()
    return f"TK-{(maximo or 4000) + 1}"


def crear(datos: dict) -> TicketSoporte:
    cliente = Cliente.query.get(datos.get("cliente_id"))
    if not cliente:
        raise TicketServiceError("Selecciona un cliente válido.")

    try:
        categoria = CategoriaTicket(datos["categoria"])
        prioridad = PrioridadTicket(datos.get("prioridad", "media"))
    except (ValueError, KeyError):
        raise TicketServiceError("Categoría o prioridad inválida.")

    ticket = TicketSoporte(
        codigo=_siguiente_codigo(),
        cliente=cliente,
        agente_id=datos.get("agente_id") or None,
        asunto=datos["asunto"].strip(),
        descripcion=datos["descripcion"].strip(),
        categoria=categoria,
        prioridad=prioridad,
        estado=EstadoTicket.ABIERTO,
    )
    db.session.add(ticket)
    db.session.flush()

    auditoria_service.registrar(
        "CREATE", "tickets_soporte", ticket.id,
        datos_nuevos={"codigo": ticket.codigo, "asunto": ticket.asunto},
    )
    db.session.commit()
    return ticket


def agregar_comentario(ticket_id: int, mensaje: str):
    ticket = TicketSoporte.query.get_or_404(ticket_id)
    if not mensaje or not mensaje.strip():
        raise TicketServiceError("El comentario no puede estar vacío.")

    comentario = ComentarioTicket(
        ticket=ticket,
        usuario_id=current_user.id if current_user.is_authenticated else None,
        mensaje=mensaje.strip(),
    )
    db.session.add(comentario)

    # Un comentario de seguimiento saca al ticket de "abierto" -> "en_proceso"
    if ticket.estado == EstadoTicket.ABIERTO:
        ticket.estado = EstadoTicket.EN_PROCESO

    db.session.commit()
    return comentario


def cambiar_estado(ticket_id: int, nuevo_estado: str):
    ticket = TicketSoporte.query.get_or_404(ticket_id)
    try:
        estado_destino = EstadoTicket(nuevo_estado)
    except ValueError:
        raise TicketServiceError("Estado inválido.")

    estado_anterior = ticket.estado
    ticket.estado = estado_destino
    if estado_destino == EstadoTicket.CERRADO:
        ticket.fecha_cierre = ahora()

    auditoria_service.registrar(
        "UPDATE", "tickets_soporte", ticket.id,
        datos_anteriores={"estado": estado_anterior.value},
        datos_nuevos={"estado": estado_destino.value},
    )
    db.session.commit()
    return ticket
