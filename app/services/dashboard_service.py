"""Servicio de reportes y KPIs avanzados (Etapa 3)."""

from datetime import timedelta
from decimal import Decimal

from sqlalchemy import func, extract

from app.extensions import db
from app.models.venta import Venta, DetalleVenta, EstadoVenta, MetodoPago
from app.time_utils import ahora
from app.models.producto import Producto
from app.models.pedido import Pedido, EstadoPedido
from app.models.atencion_cliente import TicketSoporte, EstadoTicket, CategoriaTicket
from app.models.cliente import Cliente
from app.models.movimiento_inventario import MovimientoInventario, TipoMovimiento


def kpis_principales():
    hoy = ahora()
    hace_30_dias = hoy - timedelta(days=30)
    mes_anterior = hace_30_dias - timedelta(days=30)

    def ventas_en_rango(inicio, fin):
        return (
            db.session.query(func.coalesce(func.sum(Venta.total), 0))
            .filter(Venta.estado == EstadoVenta.COMPLETADA, Venta.fecha_venta >= inicio, Venta.fecha_venta < fin)
            .scalar()
        )

    ventas_30d = ventas_en_rango(hace_30_dias, hoy)
    ventas_mes_anterior = ventas_en_rango(mes_anterior, hace_30_dias)

    numero_ventas_30d = (
        db.session.query(func.count(Venta.id))
        .filter(Venta.estado == EstadoVenta.COMPLETADA, Venta.fecha_venta >= hace_30_dias)
        .scalar()
    )

    ticket_promedio = float(ventas_30d / numero_ventas_30d) if numero_ventas_30d else 0

    crecimiento = 0
    if ventas_mes_anterior and ventas_mes_anterior > 0:
        crecimiento = ((ventas_30d - ventas_mes_anterior) / ventas_mes_anterior) * 100

    productos_stock_bajo = Producto.query.filter(
        Producto.activo.is_(True), Producto.stock_actual <= Producto.stock_minimo
    ).count()

    valor_inventario = (
        db.session.query(func.coalesce(func.sum(Producto.precio_compra * Producto.stock_actual), 0))
        .filter(Producto.activo.is_(True))
        .scalar()
    )

    return {
        "ventas_totales": float(ventas_30d),
        "numero_ventas": numero_ventas_30d,
        "ticket_promedio": ticket_promedio,
        "crecimiento": round(crecimiento, 1),
        "productos_stock_bajo": productos_stock_bajo,
        "valor_inventario": float(valor_inventario),
        "pedidos_en_camino": Pedido.query.filter(Pedido.estado == EstadoPedido.EN_CAMINO).count(),
        "tickets_abiertos": TicketSoporte.query.filter(TicketSoporte.estado != EstadoTicket.CERRADO).count(),
        "clientes_totales": Cliente.query.filter_by(activo=True).count(),
    }


def ventas_ultimos_7_dias():
    hoy = ahora()
    etiquetas, valores = [], []
    for i in range(6, -1, -1):
        dia = hoy - timedelta(days=i)
        total = (
            db.session.query(func.coalesce(func.sum(Venta.total), 0))
            .filter(
                Venta.estado == EstadoVenta.COMPLETADA,
                func.date(Venta.fecha_venta) == dia.date(),
            )
            .scalar()
        )
        etiquetas.append(dia.strftime("%d/%m"))
        valores.append(float(total))
    return etiquetas, valores


def ventas_por_categoria():
    return (
        db.session.query(
            Producto.categoria_id,
            func.sum(DetalleVenta.subtotal).label("total"),
        )
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .filter(Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(Producto.categoria_id)
        .order_by(func.sum(DetalleVenta.subtotal).desc())
        .all()
    )


def top_productos_mas_vendidos(limite=10):
    return (
        db.session.query(
            Producto.nombre,
            func.sum(DetalleVenta.cantidad).label("cantidad"),
            func.sum(DetalleVenta.subtotal).label("total"),
        )
        .join(DetalleVenta, DetalleVenta.producto_id == Producto.id)
        .join(Venta, Venta.id == DetalleVenta.venta_id)
        .filter(Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(Producto.id, Producto.nombre)
        .order_by(func.sum(DetalleVenta.cantidad).desc())
        .limit(limite)
        .all()
    )


def ventas_por_metodo_pago():
    return (
        db.session.query(
            Venta.metodo_pago,
            func.count(Venta.id).label("cantidad"),
            func.sum(Venta.total).label("total"),
        )
        .filter(Venta.estado == EstadoVenta.COMPLETADA)
        .group_by(Venta.metodo_pago)
        .all()
    )


def ventas_mensuales_12_meses():
    hoy = ahora()
    doce_meses_atras = hoy - timedelta(days=365)
    return (
        db.session.query(
            extract("year", Venta.fecha_venta).label("anio"),
            extract("month", Venta.fecha_venta).label("mes"),
            func.count(Venta.id).label("cantidad"),
            func.sum(Venta.total).label("total"),
        )
        .filter(
            Venta.estado == EstadoVenta.COMPLETADA,
            Venta.fecha_venta >= doce_meses_atras,
        )
        .group_by(extract("year", Venta.fecha_venta), extract("month", Venta.fecha_venta))
        .order_by(extract("year", Venta.fecha_venta), extract("month", Venta.fecha_venta))
        .all()
    )


def tickets_por_estado_categoria():
    return {
        "por_estado": (
            db.session.query(TicketSoporte.estado, func.count(TicketSoporte.id))
            .group_by(TicketSoporte.estado)
            .all()
        ),
        "por_categoria": (
            db.session.query(TicketSoporte.categoria, func.count(TicketSoporte.id))
            .group_by(TicketSoporte.categoria)
            .all()
        ),
    }


def productos_stock_critico(limite=20):
    return (
        Producto.query
        .filter(Producto.activo.is_(True), Producto.stock_actual <= Producto.stock_minimo)
        .order_by((Producto.stock_actual * 1.0 / func.nullif(Producto.stock_minimo, 1)).asc())
        .limit(limite)
        .all()
    )
