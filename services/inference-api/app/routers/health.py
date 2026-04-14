"""
routers/health.py — Health checks de la Inference API

🧒 PARA NIÑOS:
Igual que antes, este es el botón de "¿estás bien?"
del servicio. Kubernetes lo aprieta regularmente para
saber si debe reiniciar el servicio o si puede seguir
mandándole clientes.

📘 TÉCNICO:
Liveness y readiness probes. La readiness incluye
verificación de que el modelo esté cargado en memoria.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/health", summary="Liveness probe")
async def health_check():
    """
    🧒 PARA NIÑOS:
    Responde "estoy vivo" al recibir la pregunta.

    📘 TÉCNICO: Liveness probe para Kubernetes. Retorna 200 siempre.
    """
    return {
        "status": "healthy",
        "service": "inference-api",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get("/ready", summary="Readiness probe")
async def readiness_check(request: Request):
    """
    🧒 PARA NIÑOS:
    Responde "estoy listo para trabajar" solo cuando el modelo
    ya está cargado en memoria y puede hacer predicciones.

    📘 TÉCNICO:
    Readiness probe. Retorna 503 si el modelo no está en memoria.
    Kubernetes solo manda tráfico cuando este endpoint retorna 200.
    """
    model = getattr(request.app.state, "model", None)

    if model is None:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "inference-api",
                "reason": "Model not loaded in memory",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return {
        "status": "ready",
        "service": "inference-api",
        "model_loaded": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
