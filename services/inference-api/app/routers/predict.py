"""
routers/predict.py — Endpoint de predicción

🧒 PARA NIÑOS:
Este es el corazón de nuestro servicio: el botón mágico
que cuando lo presionas con las medidas de una flor, te
dice qué tipo de flor es. Pero primero verifica que tengas
permiso para usarlo (API Key).

📘 TÉCNICO:
Implementa POST /predict con autenticación via API Key
y rate limiting. Orquesta la llamada a prediction.py
y maneja errores de forma segura (sin exponer stack traces).
"""

import logging
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.middleware.auth import verify_api_key
from app.middleware.metrics import REQUEST_COUNT, REQUEST_DURATION
from app.models.schemas import PredictRequest, PredictResponse
from app.services.prediction import run_prediction

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post(
    "/predict",
    response_model=PredictResponse,
    summary="Predecir especie de flor Iris",
    description=(
        "Recibe las medidas de una flor Iris y retorna la especie predicha "
        "junto con el score de confianza. Requiere autenticación via X-API-Key header."
    ),
)
async def predict(
    request: Request,
    body: PredictRequest,
    _api_key: str = Depends(verify_api_key),  # Autenticación requerida
):
    """
    🧒 PARA NIÑOS:
    Esta función hace todo el trabajo:
    1. Verifica que tengas la tarjeta de acceso (API Key)
    2. Toma las medidas de tu flor
    3. Las manda a la máquina mágica (el modelo)
    4. Te devuelve el nombre de la flor y qué tan seguro está

    📘 TÉCNICO:
    Dependency injection de verify_api_key() garantiza que solo
    requests autenticadas lleguen aquí. Manejo de errores en capas:
    - 401/403: Autenticación (por verify_api_key)
    - 503: Modelo no disponible
    - 500: Error inesperado (logueado sin exponer detalles)

    Args:
        request (Request): Request de FastAPI (para acceder a app.state.model).
        body (PredictRequest): Features validadas por Pydantic.
        _api_key (str): API Key validada (inyectada por Depends).

    Returns:
        PredictResponse: Clase predicha, confianza y versión del modelo.

    Raises:
        HTTPException 503: Si el modelo no está cargado.
        HTTPException 500: Si ocurre un error inesperado durante la inferencia.
    """
    start_time = time.time()
    endpoint = "/predict"
    method = "POST"

    # Verificar que el modelo está cargado en memoria
    model = getattr(request.app.state, "model", None)
    if model is None:
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=503).inc()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="El modelo no está disponible. Inténtelo más tarde.",
        )

    # Ejecutar predicción
    try:
        features = body.model_dump()
        features_list = [
            features["sepal_length"],
            features["sepal_width"],
            features["petal_length"],
            features["petal_width"],
        ]

        prediction = run_prediction(model, features_list)

        # Registrar métricas de éxito
        duration = time.time() - start_time
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=200).inc()
        REQUEST_DURATION.labels(method=method, endpoint=endpoint).observe(duration)

        return PredictResponse(
            predicted_class=prediction["predicted_class"],
            confidence=prediction["confidence"],
            model_version=prediction["model_version"],
            input_received=features,
        )

    except Exception as e:
        # Loguear el error completo internamente pero NO exponerlo al cliente
        # (previene information disclosure)
        logger.exception("Error inesperado durante la predicción: %s", str(e))
        REQUEST_COUNT.labels(method=method, endpoint=endpoint, http_status=500).inc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno del servidor. Contacte al administrador.",
        )


@router.get(
    "/predict/example",
    summary="Ejemplo de request de predicción",
    description="Retorna un ejemplo de request válido para el endpoint /predict.",
)
async def predict_example():
    """
    🧒 PARA NIÑOS:
    Es como un ejemplo en el libro de instrucciones que muestra
    cómo usar el servicio correctamente.

    📘 TÉCNICO:
    Endpoint no autenticado que retorna un payload de ejemplo
    para facilitar la integración de nuevos clientes.
    No expone información sensible.

    Returns:
        dict: Ejemplo de request y la respuesta esperada.
    """
    return {
        "example_request": {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        },
        "expected_response": {
            "predicted_class": "setosa",
            "confidence": 0.97,
            "model_version": "1.0.0",
        },
        "note": "Incluye el header X-API-Key en tu request real.",
    }
