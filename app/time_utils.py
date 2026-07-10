"""
Utilidades de huso horario para Perú (UTC-5).

NO se almacenan timezones en la BD (SQLite no los maneja bien con
func.date()). En su lugar, todos los datetimes se guardan como naive
pero representan hora LOCAL de Perú. Así las comparaciones y
extracciones con func.date() funcionan correctamente en todos los
motores de base de datos.
"""

from datetime import datetime, timezone, timedelta

PERU_OFFSET = timedelta(hours=-5)
PERU_TZ = timezone(PERU_OFFSET, "America/Lima")


def ahora():
    """
    Retorna la fecha/hora actual de Perú como datetime NAIVE
    (sin timezone), para almacenamiento en BD.
    """
    return datetime.now(PERU_TZ).replace(tzinfo=None)


def a_peru(dt: datetime) -> datetime:
    """
    Convierte un datetime (naive-UTC o timezone-aware) a datetime
    naive que representa hora Perú.
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(PERU_TZ).replace(tzinfo=None)
