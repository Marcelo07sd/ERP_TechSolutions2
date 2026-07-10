import enum
from app.extensions import db
from app.time_utils import ahora


class TipoMovimiento(enum.Enum):
    ENTRADA = "entrada"
    SALIDA = "salida"
    AJUSTE = "ajuste"


class MovimientoInventario(db.Model):
    """
    Kardex de inventario: registro inmutable de todo cambio de stock.
    Es la fuente de verdad histórica; Producto.stock_actual es una
    proyección/caché de la suma de estos movimientos.
    """

    __tablename__ = "movimientos_inventario"

    id = db.Column(db.Integer, primary_key=True)

    producto_id = db.Column(db.Integer, db.ForeignKey("productos.id"), nullable=False)
    producto = db.relationship("Producto", back_populates="movimientos_inventario")

    tipo = db.Column(db.Enum(TipoMovimiento), nullable=False)
    cantidad = db.Column(db.Integer, nullable=False)
    stock_anterior = db.Column(db.Integer, nullable=False)
    stock_nuevo = db.Column(db.Integer, nullable=False)
    motivo = db.Column(db.String(255))
    referencia = db.Column(
        db.String(50), nullable=True
    )  # ej. número de venta que originó la salida

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=False)
    usuario = db.relationship("Usuario", back_populates="movimientos_inventario")

    fecha = db.Column(db.DateTime, default=ahora, index=True)

    __table_args__ = (
        db.CheckConstraint("cantidad > 0", name="ck_movimiento_cantidad_positiva"),
        db.Index("ix_movimiento_producto_fecha", "producto_id", "fecha"),
    )

    def __repr__(self):
        return f"<Movimiento {self.tipo.value} #{self.producto_id} ({self.cantidad})>"
