"""
Lógica de negocio del módulo Ventas.

crear_venta() es la operación más sensible del ERP: valida stock, calcula
montos, descuenta inventario (vía inventario_service, nunca tocando el
stock directamente) y dispara la creación automática del Pedido — todo
dentro de una única transacción, para que una venta nunca quede "a medias"
(por ejemplo, cobrada pero sin descontar stock).
"""

from decimal import Decimal

from flask_login import current_user
from app.time_utils import ahora
from sqlalchemy import func, cast, Integer

from app.extensions import db
from app.models.producto import Producto
from app.models.cliente import Cliente
from app.models.venta import Venta, DetalleVenta, EstadoVenta, MetodoPago
from app.models.pedido import Pedido, EstadoPedido
from app.services import auditoria_service, inventario_service

IGV = Decimal("0.18")


class VentaServiceError(Exception):
    pass


def listar(busqueda: str = "", estado: str | None = None, page: int = 1, per_page: int = 10):
    query = Venta.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.join(Cliente).filter(
            db.or_(Venta.numero_venta.ilike(like), Cliente.nombre.ilike(like), Cliente.apellido.ilike(like))
        )
    if estado:
        query = query.filter(Venta.estado == EstadoVenta(estado))
    query = query.order_by(Venta.fecha_venta.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _siguiente_numero(modelo, columna, prefijo: str, inicio: int) -> str:
    """
    Busca el máximo sufijo numérico YA USADO en `columna` (ej. 'V-2399' -> 2399)
    y devuelve el siguiente. Evita colisiones que ocurrirían si se calculara
    a partir del id de la fila (los ids no siempre coinciden 1 a 1 con la
    numeración de negocio, por ejemplo cuando no todas las ventas generan
    pedido).
    """
    largo_prefijo = len(prefijo)
    maximo = db.session.query(
        func.max(cast(func.substr(columna, largo_prefijo + 1), Integer))
    ).scalar()
    siguiente = (maximo or inicio) + 1
    return f"{prefijo}{siguiente}"


def _siguiente_numero_venta() -> str:
    return _siguiente_numero(Venta, Venta.numero_venta, "V-", 2000)


def _siguiente_numero_pedido() -> str:
    return _siguiente_numero(Pedido, Pedido.numero_pedido, "P-", 3000)


def crear_venta(cliente_id: int, metodo_pago: str, lineas: list[dict],
                 generar_pedido: bool = True, direccion_envio: str | None = None):
    """
    lineas: [{"producto_id": int, "cantidad": int}, ...]
    """
    cliente = Cliente.query.get(cliente_id)
    if not cliente:
        raise VentaServiceError("Selecciona un cliente válido.")
    if not lineas:
        raise VentaServiceError("Agrega al menos un producto a la venta.")

    try:
        metodo = MetodoPago(metodo_pago)
    except ValueError:
        raise VentaServiceError("Método de pago inválido.")

    venta = Venta(
        numero_venta=_siguiente_numero_venta(),
        cliente=cliente,
        vendedor_id=current_user.id,
        fecha_venta=ahora(),
        metodo_pago=metodo,
        estado=EstadoVenta.COMPLETADA,
        subtotal=0, igv=0, total=0,
    )
    db.session.add(venta)
    db.session.flush()

    subtotal_acumulado = Decimal("0")

    for linea in lineas:
        producto = Producto.query.get(linea.get("producto_id"))
        cantidad = int(linea.get("cantidad") or 0)

        if not producto or not producto.activo:
            raise VentaServiceError("Uno de los productos seleccionados no es válido.")
        if cantidad <= 0:
            raise VentaServiceError(f"Cantidad inválida para {producto.nombre}.")
        if cantidad > producto.stock_actual:
            raise VentaServiceError(
                f"Stock insuficiente para '{producto.nombre}': disponible {producto.stock_actual}, solicitado {cantidad}."
            )

        precio_unitario = producto.precio_venta
        sub = (precio_unitario * cantidad).quantize(Decimal("0.01"))
        subtotal_acumulado += sub

        db.session.add(
            DetalleVenta(
                venta=venta, producto=producto, cantidad=cantidad,
                precio_unitario=precio_unitario, subtotal=sub,
            )
        )

        # Descuento de stock a través del servicio de inventario, para
        # que quede el movimiento de kardex correspondiente.
        inventario_service.registrar_salida(
            producto.id, cantidad, motivo="Venta a cliente", referencia=venta.numero_venta
        )

    venta.subtotal = subtotal_acumulado.quantize(Decimal("0.01"))
    venta.igv = (venta.subtotal * IGV).quantize(Decimal("0.01"))
    venta.total = (venta.subtotal + venta.igv).quantize(Decimal("0.01"))

    if generar_pedido:
        pedido = Pedido(
            numero_pedido=_siguiente_numero_pedido(),
            venta=venta,
            cliente=cliente,
            direccion_envio=direccion_envio or cliente.direccion or "Recojo en tienda",
            ciudad_envio=cliente.ciudad,
            estado=EstadoPedido.PROCESANDO,
        )
        db.session.add(pedido)

    auditoria_service.registrar(
        "CREATE", "ventas", venta.id,
        datos_nuevos={"numero_venta": venta.numero_venta, "total": float(venta.total)},
    )

    db.session.commit()
    return venta


def anular_venta(venta_id: int, motivo: str):
    venta = Venta.query.get_or_404(venta_id)
    if venta.estado == EstadoVenta.ANULADA:
        raise VentaServiceError("Esta venta ya está anulada.")

    # Reponer stock de cada línea (entrada por anulación)
    for detalle in venta.detalles:
        inventario_service.registrar_entrada(
            detalle.producto_id, detalle.cantidad,
            motivo=f"Anulación de venta {venta.numero_venta}: {motivo}",
            referencia=venta.numero_venta,
        )

    venta.estado = EstadoVenta.ANULADA
    auditoria_service.registrar(
        "UPDATE", "ventas", venta.id,
        datos_anteriores={"estado": "completada"},
        datos_nuevos={"estado": "anulada", "motivo": motivo},
    )
    db.session.commit()
    return venta
