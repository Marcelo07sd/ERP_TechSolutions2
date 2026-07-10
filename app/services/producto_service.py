"""Lógica de negocio del módulo Productos."""

from decimal import Decimal, InvalidOperation

from app.extensions import db
from app.models.producto import Producto
from app.models.categoria import Categoria
from app.services import auditoria_service


class ProductoServiceError(Exception):
    pass


def listar(busqueda: str = "", categoria_id: int | None = None,
           solo_stock_bajo: bool = False, page: int = 1, per_page: int = 10):
    query = Producto.query
    if busqueda:
        like = f"%{busqueda}%"
        query = query.filter(
            db.or_(Producto.nombre.ilike(like), Producto.sku.ilike(like), Producto.marca.ilike(like))
        )
    if categoria_id:
        query = query.filter(Producto.categoria_id == categoria_id)
    if solo_stock_bajo:
        query = query.filter(Producto.stock_actual <= Producto.stock_minimo)

    query = query.order_by(Producto.fecha_creacion.desc())
    return query.paginate(page=page, per_page=per_page, error_out=False)


def _siguiente_sku() -> str:
    from sqlalchemy import func, cast, Integer
    maximo = db.session.query(
        func.max(cast(func.substr(Producto.sku, 4), Integer))
    ).scalar()
    siguiente_num = (maximo or 1000) + 1
    return f"TS-{siguiente_num}"


def _validar_precios(precio_compra, precio_venta):
    try:
        pc = Decimal(str(precio_compra))
        pv = Decimal(str(precio_venta))
    except (InvalidOperation, TypeError):
        raise ProductoServiceError("Los precios deben ser números válidos.")
    if pc < 0 or pv < 0:
        raise ProductoServiceError("Los precios no pueden ser negativos.")
    if pv < pc:
        raise ProductoServiceError("El precio de venta no puede ser menor al precio de compra.")
    return pc, pv


def crear(datos: dict):
    categoria = Categoria.query.get(datos.get("categoria_id"))
    if not categoria:
        raise ProductoServiceError("Selecciona una categoría válida.")

    pc, pv = _validar_precios(datos.get("precio_compra", 0), datos.get("precio_venta", 0))

    producto = Producto(
        sku=_siguiente_sku(),
        nombre=datos["nombre"].strip(),
        descripcion=(datos.get("descripcion") or "").strip(),
        categoria=categoria,
        marca=(datos.get("marca") or "").strip(),
        modelo=(datos.get("modelo") or "").strip(),
        imagen_url=(datos.get("imagen_url") or "").strip() or None,
        precio_compra=pc,
        precio_venta=pv,
        stock_actual=0,
        stock_minimo=int(datos.get("stock_minimo") or 5),
    )
    db.session.add(producto)
    db.session.flush()

    auditoria_service.registrar(
        "CREATE", "productos", producto.id,
        datos_nuevos={"sku": producto.sku, "nombre": producto.nombre},
    )
    db.session.commit()

    # El stock inicial (si se proporciona) se registra como un movimiento de
    # entrada real, nunca escribiendo directo la columna: así el kardex
    # siempre cuadra con Producto.stock_actual.
    stock_inicial = int(datos.get("stock_inicial") or 0)
    if stock_inicial > 0:
        from app.services import inventario_service
        inventario_service.registrar_entrada(
            producto.id, stock_inicial, motivo="Stock inicial al crear producto"
        )

    return producto


def actualizar(producto_id: int, datos: dict):
    producto = Producto.query.get_or_404(producto_id)
    categoria = Categoria.query.get(datos.get("categoria_id"))
    if not categoria:
        raise ProductoServiceError("Selecciona una categoría válida.")

    pc, pv = _validar_precios(datos.get("precio_compra", 0), datos.get("precio_venta", 0))

    datos_anteriores = {"nombre": producto.nombre, "precio_venta": float(producto.precio_venta)}

    producto.nombre = datos["nombre"].strip()
    producto.descripcion = (datos.get("descripcion") or "").strip()
    producto.categoria = categoria
    producto.marca = (datos.get("marca") or "").strip()
    producto.modelo = (datos.get("modelo") or "").strip()
    producto.imagen_url = (datos.get("imagen_url") or "").strip() or None
    producto.precio_compra = pc
    producto.precio_venta = pv
    producto.stock_minimo = int(datos.get("stock_minimo") or producto.stock_minimo)
    producto.activo = bool(datos.get("activo", producto.activo))

    auditoria_service.registrar(
        "UPDATE", "productos", producto.id,
        datos_anteriores=datos_anteriores,
        datos_nuevos={"nombre": producto.nombre, "precio_venta": float(producto.precio_venta)},
    )
    db.session.commit()
    return producto


def eliminar(producto_id: int):
    producto = Producto.query.get_or_404(producto_id)

    if producto.detalles_venta.count() > 0:
        raise ProductoServiceError(
            "No se puede eliminar: el producto tiene ventas asociadas. Desactívalo en su lugar."
        )

    auditoria_service.registrar(
        "DELETE", "productos", producto.id, datos_anteriores={"sku": producto.sku, "nombre": producto.nombre}
    )
    db.session.delete(producto)
    db.session.commit()
