"""
routers/model_info.py — Endpoints de información del modelo

🧒 PARA NIÑOS:
Este router es como la ficha técnica de nuestro modelo.
Cuando alguien pregunta "¿qué modelo tienes?" o "¿qué versión es?",
este archivo le responde con toda la información.

📘 TÉCNICO:
Expone endpoints REST para consultar metadatos del modelo:
versión, features esperadas, clases predichas y estado.
"""

import logging
import os

from fastapi import APIRouter, Request

from app.trainer import MODEL_VERSION, get_model_metadata

logger = logging.getLogger(__name__)

router = APIRouter()

MODEL_PATH = os.getenv("MODEL_PATH", "/app/models/iris_model.pkl")


@router.get(
    "/info",
    summary="Información del modelo",
    description="Retorna metadatos del modelo: versión, features, clases y estado.",
)
async def model_info(request: Request):
    """
    🧒 PARA NIÑOS:
    Es como leer la etiqueta de un producto en el supermercado.
    Te dice qué versión es el modelo, qué información necesita
    y qué tipos de flores puede reconocer.

    📘 TÉCNICO:
    Retorna los metadatos del modelo desde el sistema de archivos
    y el estado del modelo en memoria (app.state.model).
    No requiere autenticación ya que es información no sensible.

    Args:
        request (Request): Request de FastAPI para acceder a app.state.

    Returns:
        dict: Metadatos completos del modelo incluyendo version,
              status, class_names, feature_names y model_loaded.
    """
    metadata = get_model_metadata(MODEL_PATH)
    model_in_memory = getattr(request.app.state, "model", None) is not None

    return {
        **metadata,
        "model_loaded_in_memory": model_in_memory,
    }


@router.get(
    "/version",
    summary="Versión del modelo",
    description="Retorna solo la versión actual del modelo.",
)
async def model_version():
    """
    🧒 PARA NIÑOS:
    Devuelve solo el número de versión del modelo,
    como cuando preguntas "¿qué versión de la app tienes?".

    📘 TÉCNICO:
    Endpoint ligero que retorna solo la versión semántica
    del modelo. Útil para comparaciones rápidas en pipelines.

    Returns:
        dict: {'version': str} con la versión semántica actual.
    """
    return {"version": MODEL_VERSION}
