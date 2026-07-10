from app.extensions import db


class Categoria(db.Model):
    """
    Categorías de producto. Se agrega auto-relación (categoria_padre) para
    soportar subcategorías (ej. 'Componentes PC' > 'Tarjetas Gráficas'),
    algo estándar en catálogos de e-commerce de tecnología y que evita
    tener que crear una tabla aparte de subcategorías.
    """

    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(100), unique=True, nullable=False, index=True)
    descripcion = db.Column(db.String(255))
    categoria_padre_id = db.Column(
        db.Integer, db.ForeignKey("categorias.id"), nullable=True
    )
    activo = db.Column(db.Boolean, default=True, nullable=False)

    subcategorias = db.relationship(
        "Categoria",
        backref=db.backref("categoria_padre", remote_side=[id]),
        lazy="dynamic",
    )
    productos = db.relationship("Producto", back_populates="categoria", lazy="dynamic")

    def __repr__(self):
        return f"<Categoria {self.nombre}>"
