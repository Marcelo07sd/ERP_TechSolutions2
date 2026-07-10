import enum
from app.extensions import db
from app.time_utils import ahora


class EstadoPedido(enum.Enum):
    PROCESANDO = "procesando"
    EN_CAMINO = "en_camino"
    ENTREGADO = "entregado"
    CANCELADO = "cancelado"


class Pedido(db.Model):
    """
    Seguimiento logístico de la entrega de una venta. Se separa de Venta
    (que es un hecho contable/comercial) porque el ciclo de vida de la
    entrega es independiente: una venta se completa al cobrarse, pero el
    pedido puede seguir 'en_camino' varios días después.
    """

    __tablename__ = "pedidos"

    id = db.Column(db.Integer, primary_key=True)
    numero_pedido = db.Column(db.String(20), unique=True, nullable=False, index=True)

    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), unique=True, nullable=False)
    venta = db.relationship("Venta", back_populates="pedido")

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="pedidos")

    direccion_envio = db.Column(db.String(255), nullable=False)
    ciudad_envio = db.Column(db.String(80))

    estado = db.Column(db.Enum(EstadoPedido), default=EstadoPedido.PROCESANDO, nullable=False)
    transportista = db.Column(db.String(80))
    numero_seguimiento = db.Column(db.String(60))

    fecha_pedido = db.Column(db.DateTime, default=ahora)
    fecha_entrega_estimada = db.Column(db.Date, nullable=True)
    fecha_entrega_real = db.Column(db.DateTime, nullable=True)

    __table_args__ = (
        db.Index("ix_pedidos_estado", "estado"),
        db.Index("ix_pedidos_cliente", "cliente_id"),
    )

    def __repr__(self):
        return f"<Pedido {self.numero_pedido} - {self.estado.value}>"
