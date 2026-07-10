"""
Configuración central de la aplicación.

Decisión de arquitectura
-------------------------
Se utiliza una única configuración que decide automáticamente la base de datos:

- FLASK_ENV=development -> SQLite local en instance/techsolutions.db
- FLASK_ENV=production  -> PostgreSQL mediante DATABASE_URL (Render)

SQLAlchemy utiliza el dialecto correspondiente según la URL:
- sqlite:///
- postgresql+psycopg://
"""

import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables del archivo .env en desarrollo
load_dotenv(BASE_DIR / ".env")


class Config:
    """Configuración base común."""

    SECRET_KEY = os.environ.get(
        "SECRET_KEY",
        "dev-key-insegura-cambiar"
    )

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Paginación
    ITEMS_PER_PAGE = 10

    # Cookies
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SECURE = (
        os.environ.get("SESSION_COOKIE_SECURE", "False") == "True"
    )
    SESSION_COOKIE_SAMESITE = "Lax"


    @staticmethod
    def _build_database_uri():

        env = os.environ.get(
            "FLASK_ENV",
            "development"
        )

        database_url = os.environ.get(
            "DATABASE_URL"
        )


        # ==============================
        # PRODUCCIÓN - POSTGRESQL RENDER
        # ==============================
        if env == "production":

            if not database_url:
                raise RuntimeError(
                    "FLASK_ENV=production requiere DATABASE_URL"
                )


            # Render puede entregar:
            # postgres://
            # postgresql://
            #
            # SQLAlchemy + psycopg3 necesita:
            # postgresql+psycopg://


            if database_url.startswith("postgres://"):

                database_url = database_url.replace(
                    "postgres://",
                    "postgresql+psycopg://",
                    1
                )


            elif database_url.startswith("postgresql://"):

                database_url = database_url.replace(
                    "postgresql://",
                    "postgresql+psycopg://",
                    1
                )


            return database_url



        # ==============================
        # DESARROLLO - SQLITE LOCAL
        # ==============================

        instance_dir = BASE_DIR / "instance"

        instance_dir.mkdir(
            exist_ok=True
        )


        sqlite_path = (
            instance_dir /
            "techsolutions.db"
        )


        return f"sqlite:///{sqlite_path}"



class DevelopmentConfig(Config):

    DEBUG = True



class ProductionConfig(Config):

    DEBUG = False



class TestingConfig(Config):

    TESTING = True

    SQLALCHEMY_DATABASE_URI = (
        "sqlite:///:memory:"
    )



config_by_name = {

    "development": DevelopmentConfig,

    "production": ProductionConfig,

    "testing": TestingConfig

}



def get_config():

    env = os.environ.get(
        "FLASK_ENV",
        "development"
    )


    cfg_class = config_by_name.get(
        env,
        DevelopmentConfig
    )


    cfg_class.SQLALCHEMY_DATABASE_URI = (
        Config._build_database_uri()
    )


    return cfg_class
