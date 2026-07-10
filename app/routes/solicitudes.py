"""Rutas para el formulario web público y la recepción de pedidos."""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, current_app
from flask_login import login_required

from app.models.producto import Producto
from app.models.categoria import Categoria
from app.services import solicitud_service
from app.services.solicitud_service import SolicitudServiceError
from app.extensions import csrf

solicitudes_bp = Blueprint("solicitudes", __name__)


# --- RUTA PÚBLICA (sin login) ---

@solicitudes_bp.route("/pedir", methods=["GET"])
@csrf.exempt
def formulario():
    categorias = Categoria.query.filter_by(activo=True).order_by(Categoria.nombre).all()
    productos = Producto.query.filter_by(activo=True).order_by(Producto.nombre).all()
    return render_template("solicitudes/formulario.html", categorias=categorias, productos=productos)


@solicitudes_bp.route("/pedir", methods=["POST"])
@csrf.exempt
def enviar():
    try:
        productos_raw = []
        los_ids = request.form.getlist("producto_id[]")
        las_cants = request.form.getlist("cantidad[]")
        for pid, cant in zip(los_ids, las_cants):
            if int(cant) > 0:
                productos_raw.append({"producto_id": int(pid), "cantidad": int(cant)})

        datos = {
            "nombre": request.form.get("nombre", ""),
            "email": request.form.get("email", ""),
            "telefono": request.form.get("telefono", ""),
            "direccion": request.form.get("direccion", ""),
            "ciudad": request.form.get("ciudad", ""),
            "comentario": request.form.get("comentario", ""),
            "productos": productos_raw,
        }
        solicitud = solicitud_service.crear(datos)
        return redirect(url_for("solicitudes.exito", codigo=solicitud.codigo))
    except (SolicitudServiceError, ValueError, IndexError) as e:
        flash(str(e) or "Error al procesar el pedido.", "danger")
        return redirect(url_for("solicitudes.formulario"))


@solicitudes_bp.route("/pedir/exito")
def exito():
    codigo = request.args.get("codigo", "")
    return render_template("solicitudes/exito.html", codigo=codigo)


# --- RUTAS ADMIN (requieren login) ---

@solicitudes_bp.route("/admin/solicitudes")
@login_required
def index():
    estado = request.args.get("estado") or None
    busqueda = request.args.get("q", "").strip()
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config.get("ITEMS_PER_PAGE", 10)

    paginacion = solicitud_service.listar(estado, busqueda, page, per_page)
    return render_template(
        "solicitudes/index.html",
        solicitudes=paginacion.items,
        paginacion=paginacion,
        busqueda=busqueda,
        estado=estado,
    )


@solicitudes_bp.route("/admin/solicitudes/<int:solicitud_id>")
@login_required
def detalle(solicitud_id):
    solicitud = solicitud_service.obtener(solicitud_id)
    return render_template("solicitudes/detalle.html", solicitud=solicitud)


@solicitudes_bp.route("/admin/solicitudes/<int:solicitud_id>/aprobar", methods=["POST"])
@login_required
def aprobar(solicitud_id):
    from flask_login import current_user
    try:
        resultado = solicitud_service.aprobar(solicitud_id, current_user.id)
        flash(
            f"Pedido {resultado['venta'].numero_venta} creado correctamente.",
            "success",
        )
        return redirect(url_for("solicitudes.detalle", solicitud_id=solicitud_id))
    except SolicitudServiceError as e:
        flash(str(e), "danger")
        return redirect(url_for("solicitudes.detalle", solicitud_id=solicitud_id))


@solicitudes_bp.route("/admin/solicitudes/<int:solicitud_id>/rechazar", methods=["POST"])
@login_required
def rechazar(solicitud_id):
    from flask_login import current_user
    motivo = request.form.get("motivo", "Sin especificar")
    try:
        solicitud_service.rechazar(solicitud_id, current_user.id, motivo)
        flash("Solicitud rechazada.", "info")
        return redirect(url_for("solicitudes.detalle", solicitud_id=solicitud_id))
    except SolicitudServiceError as e:
        flash(str(e), "danger")
        return redirect(url_for("solicitudes.detalle", solicitud_id=solicitud_id))
