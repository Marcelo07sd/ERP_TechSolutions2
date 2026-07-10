"""Lógica de negocio del módulo Pedidos / Logística."""

from app.extensions import db
from app.time_utils import ahora
from app.models.pedido import Pedido, EstadoPedido
from app.services import auditoria_service

# Transiciones de estado permitidas (evita saltos ilógicos, ej. de
# "procesando" directo a "entregado" sin pasar por "en_camino").
TRANSICIONES_VALIDAS = {
    EstadoPedido.PROCESANDO: {EstadoPedido.EN_CAMINO, EstadoPedido.CANCELADO},
    EstadoPedido.EN_CAMINO: {EstadoPedido.ENTREGADO, EstadoPedido.CANCELADO},
    EstadoPedido.ENTREGADO: set(),
    EstadoPedido.CANCELADO: set(),
}


class PedidoServiceError(Exception):
    pass


def listar(busqueda: str = "", estado: str | None = None, page: int = 1, per_page: int = 10):
    from app.models.cliente import Cliente

    query = Pedido.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.join(Cliente).filter(
            db.or_(Pedido.numero_pedido.ilike(like), Cliente.nombre.ilike(like), Cliente.apellido.ilike(like))
        )
    if estado:
        query = query.filter(Pedido.estado == EstadoPedido(estado))
    query = query.order_by(Pedido.fecha_pedido.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener(pedido_id: int) -> Pedido:
    return Pedido.query.get_or_404(pedido_id)


def cambiar_estado(pedido_id: int, nuevo_estado: str, transportista: str | None = None,
                    numero_seguimiento: str | None = None):
    pedido = Pedido.query.get_or_404(pedido_id)

    try:
        estado_destino = EstadoPedido(nuevo_estado)
    except ValueError:
        raise PedidoServiceError("Estado de pedido inválido.")

    if estado_destino not in TRANSICIONES_VALIDAS.get(pedido.estado, set()):
        raise PedidoServiceError(
            f"No se puede pasar de '{pedido.estado.value}' a '{estado_destino.value}'."
        )

    estado_anterior = pedido.estado
    pedido.estado = estado_destino

    if transportista:
        pedido.transportista = transportista.strip()
    if numero_seguimiento:
        pedido.numero_seguimiento = numero_seguimiento.strip()
    if estado_destino == EstadoPedido.ENTREGADO:
        pedido.fecha_entrega_real = ahora()

    auditoria_service.registrar(
        "UPDATE", "pedidos", pedido.id,
        datos_anteriores={"estado": estado_anterior.value},
        datos_nuevos={"estado": estado_destino.value},
    )
    db.session.commit()
    return pedido
