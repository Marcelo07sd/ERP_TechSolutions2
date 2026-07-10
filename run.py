"""Punto de entrada para produccion — Gunicorn usa run:app."""
from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run()
