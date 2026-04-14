"""
models/schemas.py — Schemas Pydantic de la Inference API

🧒 PARA NIÑOS:
Los schemas son como los formularios que usamos en el banco.
Definen exactamente qué información esperamos recibir y
qué información vamos a devolver. Si alguien nos manda
un formulario incompleto o con datos raros, lo rechazamos.

📘 TÉCNICO:
Define los modelos Pydantic v2 para validación automática
de request/response. FastAPI usa estos schemas para generar
la documentación OpenAPI y validar los datos entrantes.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class PredictRequest(BaseModel):
    """
    🧒 PARA NIÑOS:
    Este es el formulario que hay que llenar para pedirle
    al modelo que reconozca una flor. Necesitas poner 4 medidas:
    largo y ancho del sépalo, y largo y ancho del pétalo.

    📘 TÉCNICO:
    Schema de entrada para POST /predict. Los valores deben
    ser flotantes positivos. Field() agrega metadata para
    la documentación OpenAPI.
    """

    sepal_length: float = Field(
        ...,
        gt=0,
        description="Largo del sépalo en centímetros",
        example=5.1,
    )
    sepal_width: float = Field(
        ...,
        gt=0,
        description="Ancho del sépalo en centímetros",
        example=3.5,
    )
    petal_length: float = Field(
        ...,
        gt=0,
        description="Largo del pétalo en centímetros",
        example=1.4,
    )
    petal_width: float = Field(
        ...,
        gt=0,
        description="Ancho del pétalo en centímetros",
        example=0.2,
    )

    model_config = {
        "json_schema_extra": {
            "example": {
                "sepal_length": 5.1,
                "sepal_width": 3.5,
                "petal_length": 1.4,
                "petal_width": 0.2,
            }
        }
    }


class PredictResponse(BaseModel):
    """
    🧒 PARA NIÑOS:
    Esta es la respuesta que te damos después de analizar
    las medidas de la flor. Te decimos qué tipo de flor es
    y qué tan seguros estamos de nuestra respuesta (en %).

    📘 TÉCNICO:
    Schema de salida para POST /predict. predicted_class es
    el nombre de la especie. confidence es el score de
    probabilidad máxima del modelo (0.0 - 1.0).
    """

    predicted_class: str = Field(
        ...,
        description="Nombre de la especie Iris predicha",
        example="setosa",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Confianza de la predicción (0.0 a 1.0)",
        example=0.97,
    )
    model_version: str = Field(
        ...,
        description="Versión del modelo que realizó la predicción",
        example="1.0.0",
    )
    input_received: dict = Field(
        ...,
        description="Echo de los datos recibidos para trazabilidad",
    )


class HealthResponse(BaseModel):
    """
    🧒 PARA NIÑOS:
    Es la respuesta a "¿estás bien?" del servicio.
    Dice si está bien (healthy) y cuándo se revisó.

    📘 TÉCNICO: Schema de respuesta para GET /health.
    """

    status: str
    service: str
    timestamp: str
    model_loaded: Optional[bool] = None
