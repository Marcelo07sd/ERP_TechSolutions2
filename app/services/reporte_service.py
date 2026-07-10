from datetime import datetime, timedelta

from app.extensions import db
from app.models.venta import Venta, EstadoVenta, DetalleVenta
from app.models.producto import Producto
from app.models.cliente import Cliente
from app.models.usuario import Usuario
from app.models.movimiento_inventario import MovimientoInventario, TipoMovimiento


class ReporteServiceError(Exception):
    pass


def resumen_ventas(desde: datetime, hasta: datetime):
    ventas = Venta.query.filter(
        Venta.fecha_venta >= desde, Venta.fecha_venta <= hasta
    ).all()
    total_ventas = len(ventas)
    total_ingresos = sum(v.total for v in ventas if v.estado != EstadoVenta.ANULADA)
    total_anuladas = sum(1 for v in ventas if v.estado == EstadoVenta.ANULADA)
    return {
        "total_ventas": total_ventas,
        "total_ingresos": total_ingresos,
        "total_anuladas": total_anuladas,
        "promedio_venta": round(total_ingresos / total_ventas, 2) if total_ventas else 0,
    }


def ventas_por_vendedor(desde: datetime, hasta: datetime):
    return (
        db.session.query(
            Usuario.id,
            Usuario.nombre,
            Usuario.apellido,
            db.func.count(Venta.id).label("cantidad"),
            db.func.sum(Venta.total).label("total"),
        )
        .join(Venta, Venta.vendedor_id == Usuario.id)
        .filter(Venta.fecha_venta >= desde, Venta.fecha_venta <= hasta, Venta.estado != EstadoVenta.ANULADA)
        .group_by(Usuario.id)
        .order_by(db.func.sum(Venta.total).desc())
        .all()
    )


def productos_mas_vendidos(desde: datetime, hasta: datetime, limite: int = 20):
    return (
        db.session.query(
            Producto.id,
            Producto.nombre,
            Producto.sku,
            db.func.sum(DetalleVenta.cantidad).label("cantidad"),
            db.func.sum(DetalleVenta.subtotal).label("total"),
        )
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .filter(Venta.fecha_venta >= desde, Venta.fecha_venta <= hasta, Venta.estado != EstadoVenta.ANULADA)
        .group_by(Producto.id)
        .order_by(db.func.sum(DetalleVenta.cantidad).desc())
        .limit(limite)
        .all()
    )


def movimientos_inventario(desde: datetime, hasta: datetime, page: int = 1, per_page: int = 20):
    query = MovimientoInventario.query.filter(
        MovimientoInventario.fecha >= desde, MovimientoInventario.fecha <= hasta
    ).order_by(MovimientoInventario.fecha.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def resumen_inventario():
    total_productos = Producto.query.filter_by(activo=True).count()
    stock_total = db.session.query(db.func.sum(Producto.stock_actual)).filter_by(activo=True).scalar() or 0
    stock_bajo = Producto.query.filter(
        Producto.activo.is_(True), Producto.stock_actual <= Producto.stock_minimo
    ).count()
    valor_inventario = (
        db.session.query(db.func.sum(Producto.stock_actual * Producto.precio_compra))
        .filter_by(activo=True)
        .scalar()
        or 0
    )
    return {
        "total_productos": total_productos,
        "stock_total": stock_total,
        "stock_bajo": stock_bajo,
        "valor_inventario": valor_inventario,
    }


def clientes_recientes(limite: int = 10):
    return Cliente.query.order_by(Cliente.fecha_registro.desc()).limit(limite).all()


def resumen_atencion():
    from app.models.atencion_cliente import TicketSoporte, EstadoTicket
    total = TicketSoporte.query.count()
    abiertos = TicketSoporte.query.filter_by(estado=EstadoTicket.ABIERTO).count()
    en_proceso = TicketSoporte.query.filter_by(estado=EstadoTicket.EN_PROCESO).count()
    cerrados = TicketSoporte.query.filter_by(estado=EstadoTicket.CERRADO).count()
    return {
        "total": total,
        "abiertos": abiertos,
        "en_proceso": en_proceso,
        "cerrados": cerrados,
    }
