from app.extensions import db
from app.models.usuario import Usuario
from app.services import auditoria_service


class UsuarioServiceError(Exception):
    pass


def listar(busqueda: str = "", page: int = 1, per_page: int = 10):
    query = Usuario.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            db.or_(
                Usuario.nombre.ilike(like),
                Usuario.apellido.ilike(like),
                Usuario.email.ilike(like),
            )
        )
    query = query.order_by(Usuario.fecha_creacion.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener(usuario_id: int) -> Usuario:
    return Usuario.query.get_or_404(usuario_id)


def crear(datos: dict) -> Usuario:
    email = datos.get("email", "").strip().lower()
    if Usuario.query.filter_by(email=email).first():
        raise UsuarioServiceError("Ya existe un usuario con ese correo.")

    usuario = Usuario(
        nombre=datos["nombre"].strip(),
        apellido=datos["apellido"].strip(),
        email=email,
        rol_id=int(datos["rol_id"]),
        activo=True,
    )
    usuario.set_password(datos["password"])
    db.session.add(usuario)
    db.session.flush()

    auditoria_service.registrar(
        "CREATE", "usuarios", usuario.id,
        datos_nuevos={"nombre": usuario.nombre_completo, "email": usuario.email},
    )
    db.session.commit()
    return usuario


def actualizar(usuario_id: int, datos: dict) -> Usuario:
    usuario = Usuario.query.get_or_404(usuario_id)
    email = datos.get("email", "").strip().lower()

    if Usuario.query.filter(Usuario.email == email, Usuario.id != usuario_id).first():
        raise UsuarioServiceError("Ya existe otro usuario con ese correo.")

    datos_anteriores = {"nombre": usuario.nombre_completo, "activo": usuario.activo}

    usuario.nombre = datos["nombre"].strip()
    usuario.apellido = datos["apellido"].strip()
    usuario.email = email
    usuario.rol_id = int(datos["rol_id"])
    usuario.activo = bool(datos.get("activo", usuario.activo))

    if datos.get("password"):
        usuario.set_password(datos["password"])

    auditoria_service.registrar(
        "UPDATE", "usuarios", usuario.id,
        datos_anteriores=datos_anteriores,
        datos_nuevos={"nombre": usuario.nombre_completo, "activo": usuario.activo},
    )
    db.session.commit()
    return usuario


def eliminar(usuario_id: int):
    usuario = Usuario.query.get_or_404(usuario_id)

    if usuario.ventas.count() > 0 or usuario.movimientos_inventario.count() > 0:
        raise UsuarioServiceError(
            "No se puede eliminar: el usuario tiene ventas o movimientos asociados. Desactívalo en su lugar."
        )

    auditoria_service.registrar(
        "DELETE", "usuarios", usuario.id,
        datos_anteriores={"nombre": usuario.nombre_completo, "email": usuario.email},
    )
    db.session.delete(usuario)
    db.session.commit()


def cambiar_password(usuario_id: int, password_actual: str, password_nueva: str):
    usuario = Usuario.query.get_or_404(usuario_id)
    if not usuario.check_password(password_actual):
        raise UsuarioServiceError("La contraseña actual no es correcta.")
    if len(password_nueva) < 6:
        raise UsuarioServiceError("La nueva contraseña debe tener al menos 6 caracteres.")
    usuario.set_password(password_nueva)
    auditoria_service.registrar(
        "UPDATE", "usuarios", usuario.id,
        datos_nuevos={"accion": "cambio de contraseña"},
    )
    db.session.commit()
