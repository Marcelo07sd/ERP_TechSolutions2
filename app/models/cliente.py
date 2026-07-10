from app.extensions import db
from app.time_utils import ahora


class Cliente(db.Model):
    """Clientes finales que compran en la tienda online."""

    __tablename__ = "clientes"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    telefono = db.Column(db.String(20))
    dni_ruc = db.Column(db.String(15), unique=True, index=True)
    direccion = db.Column(db.String(255))
    ciudad = db.Column(db.String(80))

    fecha_registro = db.Column(db.DateTime, default=ahora)
    activo = db.Column(db.Boolean, default=True, nullable=False)

    ventas = db.relationship("Venta", back_populates="cliente", lazy="dynamic")
    pedidos = db.relationship("Pedido", back_populates="cliente", lazy="dynamic")
    tickets_soporte = db.relationship(
        "TicketSoporte", back_populates="cliente", lazy="dynamic"
    )

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f"<Cliente {self.nombre_completo}>"
