"""
middleware/auth.py — Autenticación por API Key

🧒 PARA NIÑOS:
Imagina que nuestra API es como un club exclusivo.
Para entrar, necesitas mostrar tu tarjeta de membresía
(la API Key). Si no tienes tarjeta o es falsa, no puedes entrar.
Este archivo es el portero del club.

📘 TÉCNICO:
Implementa autenticación stateless con API Key usando
FastAPI Security. La clave se lee del header X-API-Key.
Comparación con timing-safe para prevenir timing attacks.
"""

import hashlib
import hmac
import logging
import os

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

logger = logging.getLogger(__name__)

# Nombre del header donde se espera la API Key
API_KEY_HEADER_NAME = "X-API-Key"

# Esquema de seguridad que FastAPI documenta en OpenAPI
api_key_header = APIKeyHeader(name=API_KEY_HEADER_NAME, auto_error=False)


def verify_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    🧒 PARA NIÑOS:
    Esta función es el portero del club. Toma la tarjeta
    que te presentas (API Key del header) y la compara con
    la lista de tarjetas válidas. Si coincide, te deja pasar.
    Si no, te dice "Lo siento, no puedes entrar."

    📘 TÉCNICO:
    Dependency injection de FastAPI para autenticación.
    Usa hmac.compare_digest() para comparación de strings
    en tiempo constante, previniendo timing attacks.
    La clave esperada se lee de la variable de entorno API_KEY.

    Args:
        api_key (str): Valor del header X-API-Key. None si ausente.

    Returns:
        str: La API key validada (para logging opcional).

    Raises:
        HTTPException 401: Si el header está ausente.
        HTTPException 403: Si la clave es incorrecta.
    """
    # Verificar que el header esté presente
    if not api_key:
        logger.warning("Request rechazada: header %s ausente", API_KEY_HEADER_NAME)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key requerida. Incluye el header X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    # Obtener la clave esperada de variables de entorno
    expected_key = os.getenv("API_KEY", "")

    if not expected_key:
        logger.error("Variable de entorno API_KEY no configurada")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Configuración de autenticación no disponible",
        )

    # Comparación en tiempo constante para prevenir timing attacks
    # (un atacante no puede saber cuántos caracteres son correctos
    # midiendo el tiempo de respuesta)
    is_valid = hmac.compare_digest(
        api_key.encode("utf-8"),
        expected_key.encode("utf-8"),
    )

    if not is_valid:
        logger.warning("Request rechazada: API Key inválida")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="API Key inválida.",
        )

    logger.debug("Autenticación exitosa")
    return api_key
