"""
main.py — Entrypoint de la Inference API

🧒 PARA NIÑOS:
Esta es la puerta principal de nuestro servicio de predicción.
Cuando alguien quiere saber qué tipo de flor tiene,
envía los datos aquí. Nosotros verificamos que sea una
persona autorizada, luego le preguntamos al modelo y
le devolvemos la respuesta.

📘 TÉCNICO:
FastAPI app principal. Gestiona el ciclo de vida (carga
del modelo en startup), registra routers, aplica middleware
de rate limiting con slowapi y expone métricas Prometheus.
"""

import logging
import os
from contextlib import asynccontextmanager

import joblib
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.middleware.metrics import MODEL_LOADED
from app.routers import health, predict

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/iris_model.pkl")

# ── Rate Limiter ──────────────────────────────────────────────
# Limita las requests por IP para proteger contra abuso
limiter = Limiter(key_func=get_remote_address)


# ── Ciclo de vida ─────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    🧒 PARA NIÑOS:
    Cuando el servicio arranca, cargamos el modelo en memoria
    para que las predicciones sean rápidas. Es como preparar
    todas las herramientas antes de abrir la tienda.

    📘 TÉCNICO:
    En startup: carga el modelo sklearn desde disco a app.state.
    MODEL_LOADED gauge de Prometheus refleja el estado.
    En shutdown: libera el modelo de memoria.
    """
    logger.info("Iniciando Inference API...")

    # Cargar modelo en memoria para serving rápido
    from pathlib import Path

    model_file = Path(MODEL_PATH)
    if model_file.exists():
        app.state.model = joblib.load(model_file)
        MODEL_LOADED.set(1)
        logger.info("Modelo cargado desde: %s", MODEL_PATH)
    else:
        app.state.model = None
        MODEL_LOADED.set(0)
        logger.warning("Modelo no encontrado en %s. El endpoint /predict fallará.", MODEL_PATH)

    yield

    logger.info("Cerrando Inference API...")
    app.state.model = None
    MODEL_LOADED.set(0)


# ── Aplicación FastAPI ────────────────────────────────────────
app = FastAPI(
    title="ML Inference API",
    description="API REST para predicción de especies Iris usando un modelo scikit-learn",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)

# ── Middleware de Rate Limiting ───────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Middleware CORS ───────────────────────────────────────────
# Solo permite orígenes conocidos (configurados via env var)
allowed_origins = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=False,  # No cookies/sessions
    allow_methods=["GET", "POST"],
    allow_headers=["X-API-Key", "Content-Type"],
)

# ── Routers ───────────────────────────────────────────────────
app.include_router(health.router, tags=["Health"])
app.include_router(predict.router, tags=["Prediction"])

# ── Métricas Prometheus en /metrics ──────────────────────────
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)
