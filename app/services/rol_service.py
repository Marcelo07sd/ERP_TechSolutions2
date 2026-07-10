from app.extensions import db
from app.models.rol import Rol
from app.services import auditoria_service


class RolServiceError(Exception):
    pass


def listar(busqueda: str = "", page: int = 1, per_page: int = 10):
    query = Rol.query
    if busqueda:
        query = query.filter(Rol.nombre.ilike(f"%{busqueda}%"))
    query = query.order_by(Rol.nombre)
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener(rol_id: int) -> Rol:
    return Rol.query.get_or_404(rol_id)


def obtener_todos():
    return Rol.query.order_by(Rol.nombre).all()


def crear(nombre: str, descripcion: str = "") -> Rol:
    if Rol.query.filter_by(nombre=nombre.strip()).first():
        raise RolServiceError("Ya existe un rol con ese nombre.")
    rol = Rol(nombre=nombre.strip(), descripcion=descripcion.strip())
    db.session.add(rol)
    db.session.flush()
    auditoria_service.registrar(
        "CREATE", "roles", rol.id, datos_nuevos={"nombre": rol.nombre}
    )
    db.session.commit()
    return rol


def actualizar(rol_id: int, nombre: str, descripcion: str = "") -> Rol:
    rol = Rol.query.get_or_404(rol_id)
    if Rol.query.filter(Rol.nombre == nombre.strip(), Rol.id != rol_id).first():
        raise RolServiceError("Ya existe otro rol con ese nombre.")
    datos_anteriores = {"nombre": rol.nombre}
    rol.nombre = nombre.strip()
    rol.descripcion = descripcion.strip()
    auditoria_service.registrar(
        "UPDATE", "roles", rol.id,
        datos_anteriores=datos_anteriores, datos_nuevos={"nombre": rol.nombre},
    )
    db.session.commit()
    return rol


def eliminar(rol_id: int):
    rol = Rol.query.get_or_404(rol_id)
    if rol.usuarios.count() > 0:
        raise RolServiceError("No se puede eliminar: hay usuarios asignados a este rol.")
    auditoria_service.registrar(
        "DELETE", "roles", rol.id, datos_anteriores={"nombre": rol.nombre}
    )
    db.session.delete(rol)
    db.session.commit()
