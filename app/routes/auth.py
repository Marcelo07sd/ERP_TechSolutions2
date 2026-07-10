from collections import defaultdict

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, login_required, current_user

from app.extensions import db
from app.models.usuario import Usuario
from app.models.auditoria import Auditoria
from app.time_utils import ahora
from app.services.usuario_service import UsuarioServiceError, cambiar_password

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

# Rate limiter simple por IP en memoria
_INTENTOS_LOGIN = defaultdict(list)
_MAX_INTENTOS = 5
_VENTANA_SEGUNDOS = 300  # 5 minutos


def _limitar_intentos(ip: str) -> bool:
    ahora_ts = ahora().timestamp()
    _INTENTOS_LOGIN[ip] = [t for t in _INTENTOS_LOGIN[ip] if ahora_ts - t < _VENTANA_SEGUNDOS]
    if len(_INTENTOS_LOGIN[ip]) >= _MAX_INTENTOS:
        return True
    _INTENTOS_LOGIN[ip].append(ahora_ts)
    return False


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard.index"))

    if request.method == "POST":
        ip = request.remote_addr or "127.0.0.1"
        if _limitar_intentos(ip):
            flash("Demasiados intentos. Espera 5 minutos.", "danger")
            return render_template("auth/login.html")

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        recordar = bool(request.form.get("recordar"))

        usuario = Usuario.query.filter_by(email=email).first()
        print("Usuario encontrado:", usuario)

        if usuario:
            print("Activo:", usuario.activo)
            print("Password correcta:", usuario.check_password(password))

        if usuario and usuario.activo and usuario.check_password(password):
            login_user(usuario, remember=recordar)
            usuario.ultimo_login = ahora()
            _INTENTOS_LOGIN.pop(ip, None)

            db.session.add(
                Auditoria(
                    usuario_id=usuario.id,
                    accion="LOGIN",
                    tabla_afectada="usuarios",
                    registro_id=usuario.id,
                    ip_address=request.remote_addr,
                )
            )
            db.session.commit()

            siguiente = request.args.get("next")
            return redirect(siguiente or url_for("dashboard.index"))

        flash("Credenciales inválidas o usuario inactivo.", "danger")

    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))


@auth_bp.route("/perfil")
@login_required
def perfil():
    return render_template("auth/perfil.html")


@auth_bp.route("/cambiar-password", methods=["POST"])
@login_required
def cambiar_password_route():
    try:
        cambiar_password(
            current_user.id,
            request.form.get("password_actual", ""),
            request.form.get("password_nueva", ""),
        )
        return jsonify({"ok": True, "mensaje": "Contraseña actualizada correctamente."})
    except UsuarioServiceError as e:
        return jsonify({"ok": False, "mensaje": str(e)}), 400
