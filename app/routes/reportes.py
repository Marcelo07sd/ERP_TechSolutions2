from datetime import timedelta

from flask import Blueprint, render_template, request, current_app
from flask_login import login_required

from app.services import reporte_service
from app.time_utils import ahora

reportes_bp = Blueprint("reportes", __name__, url_prefix="/reportes")


@reportes_bp.route("/")
@login_required
def index():
    hoy = ahora()
    periodo = request.args.get("periodo", "30")

    dias = int(periodo)
    desde = hoy - timedelta(days=dias)
    hasta = hoy

    resumen = reporte_service.resumen_ventas(desde, hasta)
    ventas_por_vendedor = reporte_service.ventas_por_vendedor(desde, hasta)
    top_productos = reporte_service.productos_mas_vendidos(desde, hasta)
    resumen_inv = reporte_service.resumen_inventario()
    clientes = reporte_service.clientes_recientes()
    resumen_atencion = reporte_service.resumen_atencion()

    return render_template(
        "reportes/index.html",
        periodo=periodo,
        desde=desde,
        hasta=hasta,
        resumen=resumen,
        ventas_por_vendedor=ventas_por_vendedor,
        top_productos=top_productos,
        resumen_inventario=resumen_inv,
        clientes_recientes=clientes,
        resumen_atencion=resumen_atencion,
    )
