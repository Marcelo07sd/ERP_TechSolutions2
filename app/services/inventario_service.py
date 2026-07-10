"""
Lógica de negocio del módulo Inventario.

Regla central del sistema: Producto.stock_actual NUNCA se edita
directamente desde una ruta. Todo cambio de stock pasa por una de las
funciones de este servicio, que además crea el MovimientoInventario
correspondiente (kardex) dentro de la MISMA transacción. Así el stock y
el historial jamás quedan desincronizados.
"""

from flask_login import current_user

from app.extensions import db
from app.models.producto import Producto
from app.models.movimiento_inventario import MovimientoInventario, TipoMovimiento
from app.services import auditoria_service


class InventarioServiceError(Exception):
    pass


def listar_movimientos(producto_id: int | None = None, tipo: str | None = None,
                        page: int = 1, per_page: int = 15):
    query = MovimientoInventario.query
    if producto_id:
        query = query.filter_by(producto_id=producto_id)
    if tipo:
        query = query.filter_by(tipo=TipoMovimiento(tipo))
    query = query.order_by(MovimientoInventario.fecha.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _crear_movimiento(producto: Producto, tipo: TipoMovimiento, cantidad: int,
                       motivo: str, referencia: str | None = None):
    stock_anterior = producto.stock_actual

    if tipo == TipoMovimiento.SALIDA:
        if cantidad > stock_anterior:
            raise InventarioServiceError(
                f"Stock insuficiente: hay {stock_anterior} unidades y se solicitan {cantidad}."
            )
        producto.stock_actual -= cantidad
    else:  # ENTRADA o AJUSTE positivo
        producto.stock_actual += cantidad

    movimiento = MovimientoInventario(
        producto=producto,
        tipo=tipo,
        cantidad=cantidad,
        stock_anterior=stock_anterior,
        stock_nuevo=producto.stock_actual,
        motivo=motivo,
        referencia=referencia,
        usuario_id=current_user.id if current_user and current_user.is_authenticated else None,
    )
    db.session.add(movimiento)
    return movimiento


def registrar_entrada(producto_id: int, cantidad: int, motivo: str, referencia: str | None = None):
    if cantidad <= 0:
        raise InventarioServiceError("La cantidad debe ser mayor a 0.")
    producto = Producto.query.get_or_404(producto_id)
    movimiento = _crear_movimiento(producto, TipoMovimiento.ENTRADA, cantidad, motivo, referencia)
    auditoria_service.registrar(
        "CREATE", "movimientos_inventario", None,
        datos_nuevos={"producto": producto.sku, "tipo": "entrada", "cantidad": cantidad},
    )
    db.session.commit()
    return movimiento


def registrar_salida(producto_id: int, cantidad: int, motivo: str, referencia: str | None = None):
    if cantidad <= 0:
        raise InventarioServiceError("La cantidad debe ser mayor a 0.")
    producto = Producto.query.get_or_404(producto_id)
    movimiento = _crear_movimiento(producto, TipoMovimiento.SALIDA, cantidad, motivo, referencia)
    auditoria_service.registrar(
        "CREATE", "movimientos_inventario", None,
        datos_nuevos={"producto": producto.sku, "tipo": "salida", "cantidad": cantidad},
    )
    db.session.commit()
    return movimiento


def registrar_ajuste(producto_id: int, nuevo_stock: int, motivo: str):
    """Ajuste manual (ej. tras un conteo físico) a un valor absoluto de stock."""
    if nuevo_stock < 0:
        raise InventarioServiceError("El stock no puede ser negativo.")

    producto = Producto.query.get_or_404(producto_id)
    diferencia = nuevo_stock - producto.stock_actual

    if diferencia == 0:
        raise InventarioServiceError("El nuevo stock es igual al actual; no hay nada que ajustar.")

    tipo = TipoMovimiento.AJUSTE
    stock_anterior = producto.stock_actual
    producto.stock_actual = nuevo_stock

    movimiento = MovimientoInventario(
        producto=producto,
        tipo=tipo,
        cantidad=abs(diferencia),
        stock_anterior=stock_anterior,
        stock_nuevo=nuevo_stock,
        motivo=motivo or "Ajuste manual de inventario",
        usuario_id=current_user.id if current_user and current_user.is_authenticated else None,
    )
    db.session.add(movimiento)

    auditoria_service.registrar(
        "UPDATE", "movimientos_inventario", None,
        datos_anteriores={"stock_anterior": stock_anterior},
        datos_nuevos={"producto": producto.sku, "tipo": "ajuste", "stock_nuevo": nuevo_stock},
    )
    db.session.commit()
    return movimiento


def productos_stock_bajo():
    return (
        Producto.query.filter(Producto.activo.is_(True), Producto.stock_actual <= Producto.stock_minimo)
        .order_by(Producto.stock_actual.asc())
        .all()
    )
