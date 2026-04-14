"""
validators.py — Validación de features del dataset Iris

🧒 PARA NIÑOS:
Este archivo es como un guardia de seguridad en la puerta.
Antes de que los datos entren a la máquina que reconoce flores,
el guardia revisa que todo esté en orden: que los números
tengan sentido y que no falte ningún dato.

📘 TÉCNICO:
Define los rangos válidos para cada feature del dataset Iris
basados en los valores reales del dataset (con un margen del 20%).
Usa Pydantic para validación de tipos y ValidationError propio
para mensajes de error descriptivos.
"""

import logging
from typing import Any

from pydantic import BaseModel, field_validator

logger = logging.getLogger(__name__)


# ── Excepción personalizada ──────────────────────────────────
class ValidationError(Exception):
    """
    🧒 PARA NIÑOS:
    Es como una nota de "datos incorrectos" que el guardia
    pone en la puerta cuando algo no está bien.

    📘 TÉCNICO:
    Excepción custom para errores de validación de features.
    Incluye el campo problemático y el valor recibido para
    facilitar el debugging.
    """

    def __init__(self, field: str, message: str, value: Any = None):
        """
        🧒 Guarda el nombre del campo problemático y el mensaje de error.

        Args:
            field (str): Nombre de la feature con el problema.
            message (str): Descripción del problema.
            value (Any): El valor inválido recibido.
        """
        self.field = field
        self.value = value
        super().__init__(f"Validation error on field '{field}': {message}. Got: {value}")


# ── Rangos válidos de features ───────────────────────────────
# Basados en el dataset Iris real con margen del 20% para flexibilidad
FEATURE_RANGES = {
    "sepal_length": {"min": 0.5, "max": 9.0},   # Real: 4.3 - 7.9 cm
    "sepal_width":  {"min": 0.5, "max": 6.0},   # Real: 2.0 - 4.4 cm
    "petal_length": {"min": 0.1, "max": 8.0},   # Real: 1.0 - 6.9 cm
    "petal_width":  {"min": 0.1, "max": 3.5},   # Real: 0.1 - 2.5 cm
}


# ── Modelo Pydantic ──────────────────────────────────────────
class IrisFeatures(BaseModel):
    """
    🧒 PARA NIÑOS:
    Este es el "formulario" que hay que llenar con las medidas
    de la flor. Tiene exactamente 4 campos: el largo y ancho
    del sépalo, y el largo y ancho del pétalo.

    📘 TÉCNICO:
    Modelo Pydantic v2 que representa las 4 features del dataset
    Iris con validación de tipos automática. Incluye método helper
    to_list() para convertir al formato numpy que espera sklearn.
    """

    sepal_length: float
    sepal_width: float
    petal_length: float
    petal_width: float

    def to_list(self) -> list:
        """
        🧒 PARA NIÑOS:
        Convierte las medidas de la flor en una lista de números
        en el orden correcto que entiende el modelo de ML.

        📘 TÉCNICO:
        Retorna las features en el orden estándar del dataset Iris:
        [sepal_length, sepal_width, petal_length, petal_width].
        Este orden debe coincidir con el usado durante el entrenamiento.

        Returns:
            list: [sepal_length, sepal_width, petal_length, petal_width]
        """
        return [self.sepal_length, self.sepal_width, self.petal_length, self.petal_width]


# ── Función principal de validación ─────────────────────────
def validate_iris_features(data: dict) -> IrisFeatures:
    """
    🧒 PARA NIÑOS:
    Esta función es el guardia principal. Toma el diccionario
    con las medidas, revisa cada número uno por uno, y si todo
    está bien, lo deja pasar. Si algo está mal, nos dice
    exactamente QUÉ está mal y POR QUÉ.

    📘 TÉCNICO:
    Valida un diccionario de features Iris en dos pasos:
    1. Validación de tipos con Pydantic (lanza ValueError si el tipo es incorrecto).
    2. Validación de rangos: cada feature debe estar dentro de FEATURE_RANGES.

    Args:
        data (dict): Diccionario con las 4 features Iris:
                     sepal_length, sepal_width, petal_length, petal_width.

    Returns:
        IrisFeatures: Objeto validado listo para enviar al modelo.

    Raises:
        ValidationError: Si alguna feature está fuera del rango permitido.
        KeyError: Si falta alguna feature requerida.
        ValueError: Si algún valor no es numérico.
    """
    # Paso 1: Validar tipos con Pydantic
    # (lanza pydantic.ValidationError si hay problemas de tipo)
    try:
        features = IrisFeatures(**data)
    except Exception as e:
        raise ValueError(f"Error de tipo en los datos de entrada: {e}") from e

    # Paso 2: Validar rangos de cada feature
    feature_values = {
        "sepal_length": features.sepal_length,
        "sepal_width":  features.sepal_width,
        "petal_length": features.petal_length,
        "petal_width":  features.petal_width,
    }

    for field_name, value in feature_values.items():
        min_val = FEATURE_RANGES[field_name]["min"]
        max_val = FEATURE_RANGES[field_name]["max"]

        if value <= 0:
            raise ValidationError(
                field=field_name,
                message=f"El valor debe ser positivo (> 0)",
                value=value,
            )

        if value < min_val or value > max_val:
            raise ValidationError(
                field=field_name,
                message=f"El valor debe estar entre {min_val} y {max_val} cm",
                value=value,
            )

    logger.debug("Features validadas exitosamente: %s", data)
    return features
