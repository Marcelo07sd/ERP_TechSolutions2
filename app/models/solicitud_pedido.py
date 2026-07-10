import enum
from app.extensions import db
from app.time_utils import ahora


class EstadoSolicitud(enum.Enum):
    PENDIENTE = "pendiente"
    APROBADO = "aprobado"
    RECHAZADO = "rechazado"


class SolicitudPedido(db.Model):
    """Pedido realizado desde el formulario web público, pendiente de
    aprobación por un administrador/vendedor."""

    __tablename__ = "solicitudes_pedido"

    id = db.Column(db.Integer, primary_key=True)
    codigo = db.Column(db.String(20), unique=True, nullable=False, index=True)

    cliente_nombre = db.Column(db.String(80), nullable=False)
    cliente_email = db.Column(db.String(120), nullable=False)
    cliente_telefono = db.Column(db.String(20))
    cliente_direccion = db.Column(db.String(255))
    cliente_ciudad = db.Column(db.String(80))

    productos_json = db.Column(db.JSON, nullable=False)
    comentario = db.Column(db.Text)

    estado = db.Column(db.Enum(EstadoSolicitud), default=EstadoSolicitud.PENDIENTE, nullable=False)
    motivo_rechazo = db.Column(db.String(255))

    atendido_por_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    atendido_por = db.relationship("Usuario")

    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=True)
    venta = db.relationship("Venta")

    fecha_creacion = db.Column(db.DateTime, default=ahora, index=True)
    fecha_atencion = db.Column(db.DateTime, nullable=True)

    @property
    def total_estimado(self):
        return sum(d["cantidad"] * d["precio_unitario"] for d in self.productos_json)

    def __repr__(self):
        return f"<SolicitudPedido {self.codigo} - {self.estado.value}>"
