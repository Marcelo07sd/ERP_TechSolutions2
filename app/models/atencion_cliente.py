import enum
from app.extensions import db
from app.time_utils import ahora


class CategoriaTicket(enum.Enum):
    RECLAMO = "reclamo"
    CONSULTA = "consulta"
    SOPORTE_TECNICO = "soporte_tecnico"
    CAMBIO_DEVOLUCION = "cambio_devolucion"


class PrioridadTicket(enum.Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class EstadoTicket(enum.Enum):
    ABIERTO = "abierto"
    EN_PROCESO = "en_proceso"
    CERRADO = "cerrado"


class TicketSoporte(db.Model):
    """Casos de atención al cliente (reclamos, consultas, soporte técnico)."""

    __tablename__ = "tickets_soporte"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="tickets_soporte")

    agente_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    agente = db.relationship("Usuario", back_populates="tickets_asignados")

    asunto = db.Column(db.String(150), nullable=False)
    descripcion = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.Enum(CategoriaTicket), nullable=False)
    prioridad = db.Column(db.Enum(PrioridadTicket), default=PrioridadTicket.MEDIA)
    estado = db.Column(db.Enum(EstadoTicket), default=EstadoTicket.ABIERTO, nullable=False)

    fecha_creacion = db.Column(db.DateTime, default=ahora, index=True)
    fecha_cierre = db.Column(db.DateTime, nullable=True)

    comentarios = db.relationship(
        "ComentarioTicket",
        back_populates="ticket",
        cascade="all, delete-orphan",
        order_by="ComentarioTicket.fecha",
    )

    __table_args__ = (
        db.Index("ix_tickets_estado", "estado"),
        db.Index("ix_tickets_prioridad", "prioridad"),
    )

    def __repr__(self):
        return f"<Ticket {self.codigo} - {self.estado.value}>"


class ComentarioTicket(db.Model):
    """
    Historial de interacciones dentro de un ticket. Se agrega esta tabla
    (no pedida explícitamente) porque un módulo de atención al cliente sin
    hilo de conversación no permite demostrar seguimiento real del caso.
    """

    __tablename__ = "comentarios_ticket"

    id = db.Column(db.Integer, primary_key=True)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets_soporte.id"), nullable=False)
    ticket = db.relationship("TicketSoporte", back_populates="comentarios")

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    usuario = db.relationship("Usuario")

    mensaje = db.Column(db.Text, nullable=False)
    fecha = db.Column(db.DateTime, default=ahora)

    def __repr__(self):
        return f"<ComentarioTicket ticket={self.ticket_id}>"
