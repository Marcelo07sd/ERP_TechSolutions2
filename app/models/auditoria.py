from app.extensions import db
from app.time_utils import ahora


class Auditoria(db.Model):
    """
    Bitácora de auditoría: registra qué usuario hizo qué acción, sobre qué
    entidad, y cuándo. Los valores antes/después se guardan como JSON para
    permitir auditar cualquier tabla sin crear una tabla de auditoría por
    entidad (evita duplicación, principio DRY).
    """

    __tablename__ = "auditoria"

    id = db.Column(db.Integer, primary_key=True)

    usuario_id = db.Column(db.Integer, db.ForeignKey("usuarios.id"), nullable=True)
    usuario = db.relationship("Usuario", back_populates="registros_auditoria")

    accion = db.Column(db.String(20), nullable=False)  # CREATE / UPDATE / DELETE / LOGIN
    tabla_afectada = db.Column(db.String(60), nullable=False, index=True)
    registro_id = db.Column(db.Integer, nullable=True)

    datos_anteriores = db.Column(db.JSON, nullable=True)
    datos_nuevos = db.Column(db.JSON, nullable=True)

    ip_address = db.Column(db.String(45))
    fecha = db.Column(db.DateTime, default=ahora, index=True)

    def __repr__(self):
        return f"<Auditoria {self.accion} {self.tabla_afectada}#{self.registro_id}>"
