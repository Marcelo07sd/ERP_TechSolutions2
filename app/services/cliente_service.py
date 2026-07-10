"""Lógica de negocio del módulo Clientes."""

from app.extensions import db
from app.models.cliente import Cliente
from app.services import auditoria_service


class ClienteServiceError(Exception):
    pass


def listar(busqueda: str = "", page: int = 1, per_page: int = 10):
    query = Cliente.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            db.or_(
                Cliente.nombre.ilike(like),
                Cliente.apellido.ilike(like),
                Cliente.email.ilike(like),
                Cliente.dni_ruc.ilike(like),
            )
        )
    query = query.order_by(Cliente.fecha_registro.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener(cliente_id: int) -> Cliente:
    return Cliente.query.get_or_404(cliente_id)


def crear(datos: dict) -> Cliente:
    if Cliente.query.filter_by(email=datos.get("email", "").strip().lower()).first():
        raise ClienteServiceError("Ya existe un cliente registrado con ese correo.")
    if datos.get("dni_ruc") and Cliente.query.filter_by(dni_ruc=datos["dni_ruc"].strip()).first():
        raise ClienteServiceError("Ya existe un cliente registrado con ese DNI/RUC.")

    cliente = Cliente(
        nombre=datos["nombre"].strip(),
        apellido=datos["apellido"].strip(),
        email=datos["email"].strip().lower(),
        telefono=(datos.get("telefono") or "").strip(),
        dni_ruc=(datos.get("dni_ruc") or "").strip() or None,
        direccion=(datos.get("direccion") or "").strip(),
        ciudad=(datos.get("ciudad") or "").strip(),
    )
    db.session.add(cliente)
    db.session.flush()

    auditoria_service.registrar(
        "CREATE", "clientes", cliente.id,
        datos_nuevos={"nombre": cliente.nombre_completo, "email": cliente.email},
    )
    db.session.commit()
    return cliente


def actualizar(cliente_id: int, datos: dict) -> Cliente:
    cliente = Cliente.query.get_or_404(cliente_id)

    duplicado_email = Cliente.query.filter(
        Cliente.email == datos.get("email", "").strip().lower(), Cliente.id != cliente_id
    ).first()
    if duplicado_email:
        raise ClienteServiceError("Ya existe otro cliente registrado con ese correo.")

    datos_anteriores = {"nombre": cliente.nombre_completo, "activo": cliente.activo}

    cliente.nombre = datos["nombre"].strip()
    cliente.apellido = datos["apellido"].strip()
    cliente.email = datos["email"].strip().lower()
    cliente.telefono = (datos.get("telefono") or "").strip()
    cliente.dni_ruc = (datos.get("dni_ruc") or "").strip() or None
    cliente.direccion = (datos.get("direccion") or "").strip()
    cliente.ciudad = (datos.get("ciudad") or "").strip()
    cliente.activo = bool(datos.get("activo", cliente.activo))

    auditoria_service.registrar(
        "UPDATE", "clientes", cliente.id,
        datos_anteriores=datos_anteriores,
        datos_nuevos={"nombre": cliente.nombre_completo, "activo": cliente.activo},
    )
    db.session.commit()
    return cliente


def eliminar(cliente_id: int):
    cliente = Cliente.query.get_or_404(cliente_id)

    if cliente.ventas.count() > 0 or cliente.tickets_soporte.count() > 0:
        raise ClienteServiceError(
            "No se puede eliminar: el cliente tiene ventas o tickets asociados. Desactívalo en su lugar."
        )

    auditoria_service.registrar(
        "DELETE", "clientes", cliente.id, datos_anteriores={"nombre": cliente.nombre_completo}
    )
    db.session.delete(cliente)
    db.session.commit()
