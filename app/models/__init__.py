"""
Se importan todos los modelos aquí para que:
1) Flask-Migrate/Alembic los detecte al autogenerar migraciones.
2) El resto de la app pueda hacer `from app.models import Usuario, Producto, ...`
   sin preocuparse por el archivo exacto donde vive cada clase.
"""

from app.models.rol import Rol
from app.models.usuario import Usuario
from app.models.cliente import Cliente
from app.models.categoria import Categoria
from app.models.producto import Producto
from app.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.models.venta import Venta, DetalleVenta, EstadoVenta, MetodoPago
from app.models.pedido import Pedido, EstadoPedido
from app.models.atencion_cliente import (
    TicketSoporte,
    ComentarioTicket,
    CategoriaTicket,
    PrioridadTicket,
    EstadoTicket,
)
from app.models.auditoria import Auditoria
from app.models.solicitud_pedido import SolicitudPedido, EstadoSolicitud

__all__ = [
    "Rol",
    "Usuario",
    "Cliente",
    "Categoria",
    "Producto",
    "MovimientoInventario",
    "TipoMovimiento",
    "Venta",
    "DetalleVenta",
    "EstadoVenta",
    "MetodoPago",
    "Pedido",
    "EstadoPedido",
    "TicketSoporte",
    "ComentarioTicket",
    "CategoriaTicket",
    "PrioridadTicket",
    "EstadoTicket",
    "Auditoria",
    "SolicitudPedido",
    "EstadoSolicitud",
]
