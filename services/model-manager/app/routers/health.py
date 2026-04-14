"""
routers/health.py — Endpoints de salud del servicio

🧒 PARA NIÑOS:
Imagina que cada servicio tiene un botón de "¿Estás bien?".
Cuando Kubernetes aprieta ese botón, el servicio responde
"¡Sí, estoy bien!" o "Me siento mal". Así Kubernetes sabe
si necesita reiniciar el servicio o mandarnos tráfico.

📘 TÉCNICO:
Implementa dos endpoints estándar de health checking:
- /health: liveness probe — ¿el proceso está vivo?
- /ready: readiness probe — ¿el servicio puede recibir tráfico?
Kubernetes usa ambos para gestionar el ciclo de vida del pod.
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Request, status
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get(
    "/health",
    summary="Liveness probe",
    description="Verifica que el proceso está vivo. Usado por Kubernetes liveness probe.",
)
async def health_check():
    """
    🧒 PARA NIÑOS:
    Es como preguntar "¿Estás despierto?". Si el servidor
    responde, significa que está vivo. Si no responde,
    Kubernetes lo reinicia.

    📘 TÉCNICO:
    Liveness probe para Kubernetes. Retorna 200 OK siempre
    que el proceso esté corriendo. No verifica dependencias.

    Returns:
        JSON con status "healthy" y timestamp UTC actual.
    """
    return {
        "status": "healthy",
        "service": "model-manager",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@router.get(
    "/ready",
    summary="Readiness probe",
    description="Verifica que el servicio está listo para recibir tráfico.",
)
async def readiness_check(request: Request):
    """
    🧒 PARA NIÑOS:
    Es como preguntar "¿Estás listo para trabajar?".
    No basta con estar despierto: el modelo tiene que estar
    cargado en memoria. Si el modelo no está listo,
    Kubernetes no manda clientes todavía.

    📘 TÉCNICO:
    Readiness probe para Kubernetes. Verifica que el modelo
    ML esté cargado en app.state.model antes de aceptar tráfico.
    Retorna 503 si el modelo no está disponible.

    Args:
        request (Request): Request de FastAPI para acceder a app.state.

    Returns:
        JSON con status "ready" o "not_ready" y detalles del modelo.
    """
    model = getattr(request.app.state, "model", None)

    if model is None:
        logger.warning("Readiness check fallido: modelo no cargado")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "not_ready",
                "service": "model-manager",
                "reason": "Model not loaded",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    return {
        "status": "ready",
        "service": "model-manager",
        "model_loaded": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
