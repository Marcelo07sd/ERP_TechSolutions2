from app.extensions import db
from app.time_utils import ahora


class Producto(db.Model):
    """Catálogo de productos tecnológicos (laptops, celulares, gamer, etc.)."""

    __tablename__ = "productos"

    id = db.Column(db.Integer, primary_key=True)
    sku = db.Column(db.String(30), unique=True, nullable=False, index=True)
    nombre = db.Column(db.String(150), nullable=False, index=True)
    descripcion = db.Column(db.Text)

    categoria_id = db.Column(db.Integer, db.ForeignKey("categorias.id"), nullable=False)
    categoria = db.relationship("Categoria", back_populates="productos")

    marca = db.Column(db.String(60))
    modelo = db.Column(db.String(60))
    imagen_url = db.Column(db.String(255))

    precio_compra = db.Column(db.Numeric(10, 2), nullable=False, default=0)
    precio_venta = db.Column(db.Numeric(10, 2), nullable=False, default=0)

    # El stock se mantiene desnormalizado aquí por rendimiento (evita sumar
    # movimientos en cada lectura), pero SIEMPRE se actualiza a través de
    # MovimientoInventario (ver InventarioService) para conservar
    # trazabilidad completa. Es la fuente de verdad para "disponibilidad",
    # mientras que la tabla de movimientos es la fuente de verdad histórica.
    stock_actual = db.Column(db.Integer, nullable=False, default=0)
    stock_minimo = db.Column(db.Integer, nullable=False, default=5)

    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=ahora)
    fecha_actualizacion = db.Column(
        db.DateTime, default=ahora, onupdate=ahora
    )

    movimientos_inventario = db.relationship(
        "MovimientoInventario", back_populates="producto", lazy="dynamic"
    )
    detalles_venta = db.relationship(
        "DetalleVenta", back_populates="producto", lazy="dynamic"
    )

    __table_args__ = (
        db.Index("ix_productos_categoria_activo", "categoria_id", "activo"),
        db.CheckConstraint("precio_venta >= 0", name="ck_producto_precio_venta_positivo"),
        db.CheckConstraint("stock_actual >= 0", name="ck_producto_stock_no_negativo"),
    )

    @property
    def stock_bajo(self) -> bool:
        return self.stock_actual <= self.stock_minimo

    def __repr__(self):
        return f"<Producto {self.sku} - {self.nombre}>"
