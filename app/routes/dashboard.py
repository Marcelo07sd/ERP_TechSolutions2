from datetime import datetime, timedelta

from flask import Blueprint, render_template
from flask_login import login_required
from sqlalchemy.orm import selectinload

from app.models.venta import Venta, MetodoPago
from app.models.categoria import Categoria
from app.services import dashboard_service

dashboard_bp = Blueprint("dashboard", __name__, url_prefix="/")


@dashboard_bp.route("/")
@login_required
def index():
    kpis = dashboard_service.kpis_principales()

    etiquetas_dias, valores_dias = dashboard_service.ventas_ultimos_7_dias()

    # --- Ventas por categoría ---
    ventas_cat = dashboard_service.ventas_por_categoria()
    categorias_dict = {c.id: c.nombre for c in Categoria.query.all()}
    cat_etiquetas = [categorias_dict.get(cat_id, f"Cat #{cat_id}") for cat_id, _ in ventas_cat]
    cat_valores = [float(v) for _, v in ventas_cat]

    # --- Top productos ---
    top_productos = dashboard_service.top_productos_mas_vendidos()
    top_nombres = [p.nombre[:30] for p in top_productos]
    top_cantidades = [p.cantidad for p in top_productos]
    top_totales = [float(p.total) for p in top_productos]

    # --- Ventas por método de pago ---
    metodos_pago = dashboard_service.ventas_por_metodo_pago()
    mp_etiquetas = [MetodoPago(mp.metodo_pago).value.capitalize() for mp in metodos_pago]
    mp_valores = [float(mp.total) for mp in metodos_pago]
    mp_colores = ["#2f6fed", "#00b894", "#f5a524", "#e5484d"][:len(mp_etiquetas)]

    # --- Ventas mensuales (12 meses) ---
    ventas_mensuales = dashboard_service.ventas_mensuales_12_meses()
    meses_nombre = ["Ene", "Feb", "Mar", "Abr", "May", "Jun",
                    "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    vm_etiquetas = [f"{meses_nombre[int(v.mes)-1]} {int(v.anio)}" for v in ventas_mensuales]
    vm_valores = [float(v.total) for v in ventas_mensuales]

    # --- Últimas ventas (con eager loading para evitar N+1) ---
    ultimas_ventas = (
        Venta.query
        .options(selectinload(Venta.cliente))
        .order_by(Venta.fecha_venta.desc())
        .limit(5)
        .all()
    )

    # --- Stock crítico ---
    stock_critico = dashboard_service.productos_stock_critico()

    return render_template(
        "dashboard/index.html",
        kpis=kpis,
        etiquetas_dias=etiquetas_dias,
        valores_dias=valores_dias,
        cat_etiquetas=cat_etiquetas,
        cat_valores=cat_valores,
        top_nombres=top_nombres,
        top_cantidades=top_cantidades,
        top_totales=top_totales,
        mp_etiquetas=mp_etiquetas,
        mp_valores=mp_valores,
        mp_colores=mp_colores,
        vm_etiquetas=vm_etiquetas,
        vm_valores=vm_valores,
        ultimas_ventas=ultimas_ventas,
        stock_critico=stock_critico,
    )
