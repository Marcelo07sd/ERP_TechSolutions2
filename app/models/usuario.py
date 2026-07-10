from flask_login import UserMixin
from app.time_utils import ahora
from werkzeug.security import generate_password_hash, check_password_hash
from app.extensions import db


class Usuario(UserMixin, db.Model):
    """
    Usuarios internos del ERP (empleados: administradores, vendedores,
    almacenistas, agentes de atención al cliente, etc.).

    UserMixin provee is_authenticated / is_active / get_id() requeridos
    por Flask-Login sin tener que reimplementarlos manualmente.
    """

    __tablename__ = "usuarios"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(80), nullable=False)
    apellido = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)

    rol_id = db.Column(db.Integer, db.ForeignKey("roles.id"), nullable=False)
    rol = db.relationship("Rol", back_populates="usuarios")

    activo = db.Column(db.Boolean, default=True, nullable=False)
    fecha_creacion = db.Column(db.DateTime, default=ahora)
    ultimo_login = db.Column(db.DateTime, nullable=True)

    # Relaciones inversas relevantes para trazabilidad
    ventas = db.relationship("Venta", back_populates="vendedor", lazy="dynamic")
    movimientos_inventario = db.relationship(
        "MovimientoInventario", back_populates="usuario", lazy="dynamic"
    )
    tickets_asignados = db.relationship(
        "TicketSoporte", back_populates="agente", lazy="dynamic"
    )
    registros_auditoria = db.relationship(
        "Auditoria", back_populates="usuario", lazy="dynamic"
    )

    __table_args__ = (
        db.Index("ix_usuarios_email_activo", "email", "activo"),
    )

    # ---------- Password helpers ----------
    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    @property
    def nombre_completo(self) -> str:
        return f"{self.nombre} {self.apellido}"

    def __repr__(self):
        return f"<Usuario {self.email}>"
