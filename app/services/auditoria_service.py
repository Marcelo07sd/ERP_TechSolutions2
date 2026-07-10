"""
Servicio transversal de auditoría. Se usa desde el resto de servicios para
no repetir en cada uno la construcción manual de un registro de Auditoria
(DRY): cualquier módulo que necesite dejar traza de un CREATE/UPDATE/DELETE
llama a `registrar()`.
"""

from flask import request
from flask_login import current_user

from app.extensions import db
from app.models.auditoria import Auditoria


def registrar(accion: str, tabla_afectada: str, registro_id=None,
              datos_anteriores: dict | None = None,
              datos_nuevos: dict | None = None) -> None:
    usuario_id = current_user.id if current_user and current_user.is_authenticated else None
    ip = request.remote_addr if request else None

    db.session.add(
        Auditoria(
            usuario_id=usuario_id,
            accion=accion,
            tabla_afectada=tabla_afectada,
            registro_id=registro_id,
            datos_anteriores=datos_anteriores,
            datos_nuevos=datos_nuevos,
            ip_address=ip,
        )
    )


def listar(tabla: str | None = None, accion: str | None = None, usuario_id: int | None = None,
           page: int = 1, per_page: int = 20):
    """Listado de solo lectura para el módulo Auditoría (nunca se edita ni
    elimina un registro de auditoría, por diseño: es la fuente de verdad
    de 'quién hizo qué y cuándo')."""
    query = Auditoria.query
    if tabla:
        query = query.filter(Auditoria.tabla_afectada == tabla)
    if accion:
        query = query.filter(Auditoria.accion == accion)
    if usuario_id:
        query = query.filter(Auditoria.usuario_id == usuario_id)
    query = query.order_by(Auditoria.fecha.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def tablas_disponibles() -> list[str]:
    filas = db.session.query(Auditoria.tabla_afectada).distinct().order_by(Auditoria.tabla_afectada).all()
    return [f[0] for f in filas]
