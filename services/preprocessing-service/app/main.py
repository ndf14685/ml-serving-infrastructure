"""
main.py — Entrypoint del Preprocessing Service

🧒 PARA NIÑOS:
Este servicio es como un lavaplatos automático para datos.
Antes de que los datos de las flores lleguen a la máquina
que las reconoce, pasan por aquí para ser limpiados,
validados y preparados correctamente.

📘 TÉCNICO:
FastAPI app que expone un endpoint POST /preprocess.
Valida y normaliza las features Iris antes de enviarlas
al inference service. Emite métricas Prometheus.
"""

import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, status
from prometheus_client import Counter, Histogram, make_asgi_app
from pydantic import BaseModel

from app.validators import IrisFeatures, ValidationError, validate_iris_features

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

# ── Métricas Prometheus ──────────────────────────────────────
preprocess_requests = Counter(
    "preprocessing_requests_total",
    "Total de requests de preprocesamiento",
    ["status"],  # labels: success | validation_error
)

preprocess_duration = Histogram(
    "preprocessing_duration_seconds",
    "Duración del preprocesamiento en segundos",
)


# ── Schemas de request/response ──────────────────────────────
class PreprocessRequest(BaseModel):
    """
    🧒 PARA NIÑOS:
    Este es el sobre que llega con las medidas de la flor.
    Tiene exactamente 4 datos adentro.

    📘 TÉCNICO: Schema de entrada para el endpoint /preprocess.
    """

    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float


class PreprocessResponse(BaseModel):
    """
    🧒 PARA NIÑOS:
    Este es el sobre de respuesta que enviamos después
    de revisar y limpiar los datos. Contiene los datos
    listos para el modelo.

    📘 TÉCNICO: Schema de salida del endpoint /preprocess.
    features_array es la lista ordenada lista para numpy.
    """

    features_array: list
    original_input: dict
    validation_passed: bool


# ── Aplicación FastAPI ───────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    🧒 PARA NIÑOS:
    Acciones de inicio y cierre del servicio.

    📘 TÉCNICO: Lifecycle manager de FastAPI.
    """
    logger.info("Iniciando Preprocessing Service...")
    yield
    logger.info("Cerrando Preprocessing Service...")


app = FastAPI(
    title="Preprocessing Service",
    description="Valida y transforma features Iris antes de la inferencia",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if os.getenv("ENVIRONMENT", "development") != "production" else None,
    redoc_url=None,
)

# Montar métricas Prometheus
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# ── Endpoints ────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health_check():
    """
    🧒 PARA NIÑOS:
    Responde "estoy bien" cuando alguien pregunta.

    📘 TÉCNICO: Liveness probe para Kubernetes.
    """
    from datetime import datetime, timezone

    return {
        "status": "healthy",
        "service": "preprocessing-service",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.post("/preprocess", response_model=PreprocessResponse, tags=["Preprocessing"])
async def preprocess(request: PreprocessRequest):
    """
    🧒 PARA NIÑOS:
    Recibe las medidas de una flor, las revisa para ver
    si tienen sentido, y si todo está bien las devuelve
    en el formato correcto para que el modelo las entienda.

    📘 TÉCNICO:
    Valida las features con validate_iris_features() y
    retorna el array de features en el orden correcto
    para sklearn. Si la validación falla, retorna 422.

    Args:
        request (PreprocessRequest): Features crudas de la flor.

    Returns:
        PreprocessResponse: Features validadas como lista.

    Raises:
        HTTPException 422: Si alguna feature está fuera de rango.
    """
    input_dict = request.model_dump()

    try:
        with preprocess_duration.time():
            validated: IrisFeatures = validate_iris_features(input_dict)

        preprocess_requests.labels(status="success").inc()

        return PreprocessResponse(
            features_array=validated.to_list(),
            original_input=input_dict,
            validation_passed=True,
        )

    except ValidationError as e:
        preprocess_requests.labels(status="validation_error").inc()
        logger.warning("Validación fallida: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Validation failed", "field": e.field, "message": str(e)},
        )
