"""Servicio de solicitudes de pedido desde el formulario web público."""

from datetime import datetime
from decimal import Decimal
from sqlalchemy import func, cast, Integer

from app.extensions import db
from app.models.solicitud_pedido import SolicitudPedido, EstadoSolicitud
from app.models.producto import Producto
from app.models.cliente import Cliente
from app.models.venta import Venta, DetalleVenta, EstadoVenta, MetodoPago
from app.models.pedido import Pedido, EstadoPedido
from app.services import auditoria_service, inventario_service
from app.services.venta_service import _siguiente_numero_venta, _siguiente_numero_pedido
from app.time_utils import ahora


class SolicitudServiceError(Exception):
    pass


def _siguiente_codigo() -> str:
    maximo = db.session.query(
        func.max(cast(func.substr(SolicitudPedido.codigo, 3), Integer))
    ).scalar()
    return f"W-{(maximo or 1000) + 1}"


def listar(estado: str | None = None, busqueda: str = "", page: int = 1, per_page: int = 10):
    query = SolicitudPedido.query
    if estado:
        query = query.filter(SolicitudPedido.estado == EstadoSolicitud(estado))
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            db.or_(
                SolicitudPedido.codigo.ilike(like),
                SolicitudPedido.cliente_nombre.ilike(like),
                SolicitudPedido.cliente_email.ilike(like),
            )
        )
    query = query.order_by(SolicitudPedido.fecha_creacion.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener(solicitud_id: int) -> SolicitudPedido:
    return SolicitudPedido.query.get_or_404(solicitud_id)


def crear(datos: dict) -> SolicitudPedido:
    productos_raw = datos.get("productos", [])
    if not productos_raw:
        raise SolicitudServiceError("Debes seleccionar al menos un producto.")

    productos = []
    for item in productos_raw:
        prod = Producto.query.get(item.get("producto_id"))
        if not prod or not prod.activo:
            raise SolicitudServiceError(f"Producto ID {item.get('producto_id')} no encontrado.")
        cantidad = int(item.get("cantidad", 1))
        if cantidad < 1:
            raise SolicitudServiceError("La cantidad debe ser al menos 1.")
        productos.append({
            "producto_id": prod.id,
            "sku": prod.sku,
            "nombre": prod.nombre,
            "cantidad": cantidad,
            "precio_unitario": float(prod.precio_venta),
        })

    solicitud = SolicitudPedido(
        codigo=_siguiente_codigo(),
        cliente_nombre=datos.get("nombre", "").strip(),
        cliente_email=datos.get("email", "").strip().lower(),
        cliente_telefono=datos.get("telefono", "").strip(),
        cliente_direccion=datos.get("direccion", "").strip(),
        cliente_ciudad=datos.get("ciudad", "").strip(),
        productos_json=productos,
        comentario=datos.get("comentario", "").strip(),
        estado=EstadoSolicitud.PENDIENTE,
    )
    db.session.add(solicitud)
    db.session.commit()
    return solicitud


def aprobar(solicitud_id: int, usuario_id: int) -> dict:
    solicitud = SolicitudPedido.query.get_or_404(solicitud_id)
    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise SolicitudServiceError(f"La solicitud ya fue {solicitud.estado.value}.")

    solicitud.estado = EstadoSolicitud.APROBADO
    solicitud.atendido_por_id = usuario_id
    solicitud.fecha_atencion = ahora()

    productos_data = solicitud.productos_json
    cliente = Cliente.query.filter_by(email=solicitud.cliente_email).first()
    if not cliente:
        cliente = Cliente(
            nombre=solicitud.cliente_nombre.split()[0] if " " in solicitud.cliente_nombre else solicitud.cliente_nombre,
            apellido=" ".join(solicitud.cliente_nombre.split()[1:]) if " " in solicitud.cliente_nombre else "",
            email=solicitud.cliente_email,
            telefono=solicitud.cliente_telefono,
            direccion=solicitud.cliente_direccion,
            ciudad=solicitud.cliente_ciudad,
        )
        db.session.add(cliente)
        db.session.flush()

    subtotal = Decimal("0")
    IGV = Decimal("0.18")
    detalles = []
    for item in productos_data:
        prod = Producto.query.get(item["producto_id"])
        if not prod:
            continue
        cantidad = item["cantidad"]
        precio = Decimal(str(item["precio_unitario"]))
        sub = (precio * cantidad).quantize(Decimal("0.01"))
        subtotal += sub
        detalles.append({
            "producto": prod,
            "cantidad": cantidad,
            "precio_unitario": precio,
            "subtotal": sub,
        })

    igv = (subtotal * IGV).quantize(Decimal("0.01"))
    total = (subtotal + igv).quantize(Decimal("0.01"))

    venta = Venta(
        numero_venta=_siguiente_numero_venta(),
        cliente=cliente,
        vendedor_id=usuario_id,
        fecha_venta=ahora(),
        metodo_pago=MetodoPago.PENDIENTE,
        estado=EstadoVenta.COMPLETADA,
        subtotal=subtotal,
        igv=igv,
        total=total,
    )
    db.session.add(venta)
    db.session.flush()

    for d in detalles:
        db.session.add(DetalleVenta(
            venta=venta,
            producto=d["producto"],
            cantidad=d["cantidad"],
            precio_unitario=d["precio_unitario"],
            subtotal=d["subtotal"],
        ))
        inventario_service.registrar_salida(
            producto_id=d["producto"].id,
            cantidad=d["cantidad"],
            motivo=f"Pedido web {solicitud.codigo}",
            referencia=venta.numero_venta,
        )

    pedido = Pedido(
        numero_pedido=_siguiente_numero_pedido(),
        venta=venta,
        cliente=cliente,
        direccion_envio=solicitud.cliente_direccion or "Por definir",
        ciudad_envio=solicitud.cliente_ciudad or "Lima",
        estado=EstadoPedido.PROCESANDO,
        fecha_pedido=ahora(),
    )
    db.session.add(pedido)
    solicitud.venta_id = venta.id

    auditoria_service.registrar(
        "UPDATE", "solicitudes_pedido", solicitud.id,
        datos_anteriores={"estado": "pendiente"},
        datos_nuevos={"estado": "aprobado", "venta_id": venta.id},
    )
    db.session.commit()
    return {"venta": venta, "pedido": pedido}


def rechazar(solicitud_id: int, usuario_id: int, motivo: str):
    solicitud = SolicitudPedido.query.get_or_404(solicitud_id)
    if solicitud.estado != EstadoSolicitud.PENDIENTE:
        raise SolicitudServiceError(f"La solicitud ya fue {solicitud.estado.value}.")

    solicitud.estado = EstadoSolicitud.RECHAZADO
    solicitud.motivo_rechazo = motivo
    solicitud.atendido_por_id = usuario_id
    solicitud.fecha_atencion = ahora()

    auditoria_service.registrar(
        "UPDATE", "solicitudes_pedido", solicitud.id,
        datos_anteriores={"estado": "pendiente"},
        datos_nuevos={"estado": "rechazado", "motivo": motivo},
    )
    db.session.commit()
