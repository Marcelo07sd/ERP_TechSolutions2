"""
Configuración central de la aplicación.

Decisión de arquitectura
-------------------------
En lugar de tener dos archivos de configuración distintos (uno por motor de
base de datos), se usa UNA sola fuente de verdad (`Config`) que arma la
`SQLALCHEMY_DATABASE_URI` a partir de variables de entorno. Así, SQLAlchemy
(con sus dialectos `sqlite` y `postgresql`) es el único responsable de
traducir el mismo código de modelos/consultas a cada motor. El código de la
aplicación nunca sabe (ni le importa) contra qué base de datos corre.

- FLASK_ENV=development  -> SQLite local en instance/techsolutions.db
- FLASK_ENV=production   -> PostgreSQL vía DATABASE_URL (Render u otro host)
"""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuración base común a todos los entornos."""

    SECRET_KEY = os.environ.get("SECRET_KEY", "dev-key-insegura-cambiar")
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paginación estándar para listados del ERP
    ITEMS_PER_PAGE = 10

    # Cookies de sesión
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
    SESSION_COOKIE_SAMESITE = "Lax"

    @staticmethod
    def _build_database_uri() -> str:
        env = os.environ.get("FLASK_ENV", "development")
        database_url = os.environ.get("DATABASE_URL")

        if env == "production":
            if not database_url:
                raise RuntimeError(
                    "FLASK_ENV=production requiere DATABASE_URL "
                    "apuntando a PostgreSQL (ej. instancia de Render)."
                )
            # Render entrega a veces 'postgres://', SQLAlchemy 1.4+/2.x
            # requiere el prefijo 'postgresql://'
            if database_url.startswith("postgres://"):
                database_url = database_url.replace(
                    "postgres://", "postgresql+psycopg://", 1
                )
            return database_url

        # Desarrollo / testing local -> SQLite dentro de instance/
        instance_dir = BASE_DIR / "instance"
        instance_dir.mkdir(exist_ok=True)
        sqlite_path = instance_dir / "techsolutions.db"
        return f"sqlite:///{sqlite_path}"

    SQLALCHEMY_DATABASE_URI = None  # se asigna dinámicamente en init


class DevelopmentConfig(Config):
    DEBUG = True


class ProductionConfig(Config):
    DEBUG = False


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


config_by_name = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig,
}


def get_config():
    env = os.environ.get("FLASK_ENV", "development")
    cfg_class = config_by_name.get(env, DevelopmentConfig)
    cfg_class.SQLALCHEMY_DATABASE_URI = Config._build_database_uri()
    return cfg_class
