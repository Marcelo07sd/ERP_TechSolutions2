from app.extensions import db
from app.time_utils import ahora


class Rol(db.Model):
    """Roles del sistema (control de acceso basado en roles - RBAC)."""

    __tablename__ = "roles"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(255))
    fecha_creacion = db.Column(db.DateTime, default=ahora)

    usuarios = db.relationship("Usuario", back_populates="rol", lazy="dynamic")

    def __repr__(self):
        return f"<Rol {self.nombre}>"
