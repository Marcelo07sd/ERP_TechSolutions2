"""Lógica de negocio del módulo Categorías."""

from app.extensions import db
from app.models.categoria import Categoria
from app.services import auditoria_service


class CategoriaServiceError(Exception):
    """Errores de negocio del módulo Categorías (se muestran al usuario)."""


def listar(busqueda: str = "", page: int = 1, per_page: int = 10):
    query = Categoria.query
    if busqueda:
        query = query.filter(Categoria.nombre.ilike(f"%{busqueda}%"))
    query = query.order_by(Categoria.categoria_padre_id.is_(None).desc(), Categoria.nombre)
    return query.paginate(page=page, per_page=per_page, error_out=False)


def obtener_opciones_padre(excluir_id: int | None = None):
    """Categorías que pueden actuar como padre (no se permite auto-referencia)."""
    query = Categoria.query.filter(Categoria.categoria_padre_id.is_(None))
    if excluir_id:
        query = query.filter(Categoria.id != excluir_id)
    return query.order_by(Categoria.nombre).all()


def crear(nombre: str, descripcion: str, categoria_padre_id: int | None):
    if Categoria.query.filter_by(nombre=nombre).first():
        raise CategoriaServiceError(f"Ya existe una categoría llamada '{nombre}'.")

    categoria = Categoria(
        nombre=nombre.strip(),
        descripcion=(descripcion or "").strip(),
        categoria_padre_id=categoria_padre_id or None,
    )
    db.session.add(categoria)
    db.session.flush()

    auditoria_service.registrar(
        "CREATE", "categorias", categoria.id,
        datos_nuevos={"nombre": categoria.nombre, "categoria_padre_id": categoria.categoria_padre_id},
    )
    db.session.commit()
    return categoria


def actualizar(categoria_id: int, nombre: str, descripcion: str,
                categoria_padre_id: int | None, activo: bool):
    categoria = Categoria.query.get_or_404(categoria_id)

    duplicado = Categoria.query.filter(
        Categoria.nombre == nombre, Categoria.id != categoria_id
    ).first()
    if duplicado:
        raise CategoriaServiceError(f"Ya existe una categoría llamada '{nombre}'.")

    if categoria_padre_id == categoria_id:
        raise CategoriaServiceError("Una categoría no puede ser su propia categoría padre.")

    datos_anteriores = {"nombre": categoria.nombre, "activo": categoria.activo}

    categoria.nombre = nombre.strip()
    categoria.descripcion = (descripcion or "").strip()
    categoria.categoria_padre_id = categoria_padre_id or None
    categoria.activo = activo

    auditoria_service.registrar(
        "UPDATE", "categorias", categoria.id,
        datos_anteriores=datos_anteriores,
        datos_nuevos={"nombre": categoria.nombre, "activo": categoria.activo},
    )
    db.session.commit()
    return categoria


def eliminar(categoria_id: int):
    categoria = Categoria.query.get_or_404(categoria_id)

    if categoria.productos.count() > 0:
        raise CategoriaServiceError(
            "No se puede eliminar: la categoría tiene productos asociados. "
            "Desactívala en su lugar."
        )
    if categoria.subcategorias.count() > 0:
        raise CategoriaServiceError(
            "No se puede eliminar: tiene subcategorías asociadas."
        )

    auditoria_service.registrar(
        "DELETE", "categorias", categoria.id, datos_anteriores={"nombre": categoria.nombre}
    )
    db.session.delete(categoria)
    db.session.commit()
