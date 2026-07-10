import enum
from app.extensions import db
from app.time_utils import ahora


class EstadoVenta(enum.Enum):
    PENDIENTE = "pendiente"
    COMPLETADA = "completada"
    ANULADA = "anulada"


class MetodoPago(enum.Enum):
    PENDIENTE = "pendiente"
    EFECTIVO = "efectivo"
    TARJETA = "tarjeta"
    TRANSFERENCIA = "transferencia"
    YAPE_PLIN = "yape_plin"


class Venta(db.Model):
    """Cabecera de una venta (transacción comercial)."""

    __tablename__ = "ventas"

    id = db.Column(db.Integer, primary_key=True)
    numero_venta = db.Column(db.String(20), unique=True, nullable=False, index=True)

    cliente_id = db.Column(db.Integer, db.ForeignKey("clientes.id"), nullable=False)
    cliente = db.relationship("Cliente", back_populates="ventas")

    vendedor_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    vendedor = db.relationship("Usuario", back_populates="ventas")

    fecha_venta = db.Column(db.DateTime, default=ahora, index=True)

    subtotal = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    igv = db.Column(db.Numeric(10, 2), nullable=False, default=0)  # IGV Perú 18%
    total = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    estado = db.Column(
        db.Enum(EstadoVenta), nullable=False, default=EstadoVenta.PENDIENTE
    )
    metodo_pago = db.Column(db.Enum(MetodoPago), nullable=False)

    detalles = db.relationship(
        "DetalleVenta",
        back_populates="venta",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    pedido = db.relationship(
        "Pedido", back_populates="venta", uselist=False, lazy="joined"
    )

    __table_args__ = (
        db.Index("ix_ventas_cliente_fecha", "cliente_id", "fecha_venta"),
        db.Index("ix_ventas_estado_fecha", "estado", "fecha_venta"),
    )

    def __repr__(self):
        return f"<Venta {self.numero_venta} - {self.estado.value}>"


class DetalleVenta(db.Model):
    """Líneas de detalle de una venta (productos, cantidades, precios)."""

    __tablename__ = "detalle_ventas"

    id = db.Column(db.Integer, primary_key=True)

    venta_id = db.Column(db.Integer, db.ForeignKey("ventas.id"), nullable=False)
    venta = db.relationship("Venta", back_populates="detalles")

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="detalles_venta")

    cantidad = db.Column(db.Integer, nullable=False)
    precio_unitario = db.Column(db.Numeric(10, 2), nullable=False)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)

    __table_args__ = (
        db.CheckConstraint("cantidad > 0", name="ck_detalle_cantidad_positiva"),
        db.Index("ix_detalle_venta_id", "venta_id"),
        db.Index("ix_detalle_producto_id", "producto_id"),
    )

    def __repr__(self):
        return f"<DetalleVenta venta={self.venta_id} producto={self.producto_id}>"
