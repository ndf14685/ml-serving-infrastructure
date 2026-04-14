"""
main.py — Entrypoint del Model Manager Service

🧒 PARA NIÑOS:
Este es el "mostrador" de nuestra tienda de modelos.
Cuando alguien quiere saber información del modelo
o pedir que se entrene uno nuevo, viene aquí.
Es como la recepción de un edificio: dirige a cada
persona al lugar correcto.

📘 TÉCNICO:
Inicializa la aplicación FastAPI, configura el ciclo
de vida (entrenamiento del modelo al arrancar), registra
los routers y expone las métricas de Prometheus.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from prometheus_client import make_asgi_app

from app.routers import health, model_info
from app.trainer import load_model, train_model

# ── Configuración de logging ─────────────────────────────────
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Ruta del modelo (configurable via variable de entorno)
MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/iris_model.pkl")


# ── Ciclo de vida de la aplicación ───────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    🧒 PARA NIÑOS:
    Esto es como el botón de encendido y apagado de la tienda.
    Cuando abrimos, entrenamos el modelo si no está listo.
    Cuando cerramos, hacemos la limpieza.

    📘 TÉCNICO:
    Gestiona el startup y shutdown de la aplicación FastAPI.
    En startup: verifica si existe el modelo; si no, lo entrena.
    Almacena el modelo en el estado de la app para evitar
    recargas innecesarias entre requests.
    """
    # STARTUP: cargar o entrenar el modelo
    logger.info("Iniciando Model Manager Service...")

    model = load_model(MODEL_PATH)
    if model is None:
        logger.info("Modelo no encontrado. Iniciando entrenamiento...")
        metrics = train_model(MODEL_PATH)
        logger.info("Modelo entrenado con accuracy: %.4f", metrics["accuracy"])
        model = load_model(MODEL_PATH)

    # Guardar modelo en el estado de la app (evita recargar en cada request)
    app.state.model = model
    app.state.model_path = MODEL_PATH

    logger.info("Model Manager listo")
    yield

    # SHUTDOWN: limpieza
    logger.info("Cerrando Model Manager Service...")
    app.state.model = None


# ── Aplicación FastAPI ───────────────────────────────────────
app = FastAPI(
    title="Model Manager Service",
    description="Gestiona versiones y metadatos del modelo ML Iris",
    version="1.0.0",
    lifespan=lifespan,
    # En producción, ocultar el schema para no exponer la API públicamente
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)

# ── Registrar routers ────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(model_info.router, prefix="/model", tags=["Model"])

# ── Exponer métricas de Prometheus en /metrics ───────────────
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
