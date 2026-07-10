from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash("Por favor inicia sesión para continuar.", "warning")
            return redirect(url_for("auth.login"))
        if current_user.rol.nombre != "Administrador":
            flash("No tienes permisos para acceder a esta sección.", "danger")
            return redirect(url_for("dashboard.index"))
        return f(*args, **kwargs)
    return decorated_function
