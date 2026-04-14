"""
services/prediction.py — Lógica de negocio de predicción

🧒 PARA NIÑOS:
Este archivo es el cerebro de nuestra operación. Recibe
las medidas de una flor, se las pasa al modelo mágico,
y te dice qué tipo de flor es. También lleva la cuenta
de cuántas predicciones hizo y con qué confianza.

📘 TÉCNICO:
Orquesta el flujo completo de predicción: carga el modelo
desde el estado de la app, ejecuta predict_proba() de sklearn,
convierte el resultado a nombre de clase y emite métricas.
Desacoplado del router para facilitar testing unitario.
"""

import logging
import os
from typing import Optional

import numpy as np

from app.middleware.metrics import MODEL_LOADED, PREDICTION_CONFIDENCE, PREDICTION_COUNT

logger = logging.getLogger(__name__)

# Nombres de clases en el mismo orden que el modelo sklearn
IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]
MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")


def run_prediction(model, features: list) -> dict:
    """
    🧒 PARA NIÑOS:
    Esta función toma las medidas de la flor (4 números)
    y las mete en la máquina mágica (el modelo). La máquina
    piensa un momento y luego dice "¡Es una setosa!" con
    un porcentaje de qué tan segura está.

    📘 TÉCNICO:
    Ejecuta predict_proba() sobre el pipeline sklearn.
    Retorna la clase con mayor probabilidad (argmax) y
    su score de confianza. Emite métricas Prometheus.

    Args:
        model: Pipeline sklearn cargado y listo para predict.
        features (list): Lista de 4 floats en orden:
                         [sepal_length, sepal_width, petal_length, petal_width]

    Returns:
        dict: {
            'predicted_class': str,   # Nombre de la especie
            'confidence': float,       # Score 0.0 - 1.0
            'model_version': str,      # Versión del modelo
        }

    Raises:
        ValueError: Si features tiene longitud incorrecta.
        RuntimeError: Si el modelo falla durante la inferencia.
    """
    if len(features) != 4:
        raise ValueError(
            f"Se esperaban 4 features, se recibieron {len(features)}"
        )

    # Convertir a array numpy con la forma correcta para sklearn: (1, 4)
    features_array = np.array([features])

    # Ejecutar inferencia y obtener probabilidades por clase
    try:
        probabilities = model.predict_proba(features_array)[0]
    except Exception as e:
        raise RuntimeError(f"Error durante la inferencia del modelo: {e}") from e

    # Obtener la clase con mayor probabilidad
    predicted_index = int(np.argmax(probabilities))
    confidence = float(probabilities[predicted_index])
    predicted_class = IRIS_CLASS_NAMES[predicted_index]

    logger.info(
        "Predicción: clase=%s, confianza=%.4f",
        predicted_class,
        confidence,
    )

    # Emitir métricas
    PREDICTION_COUNT.labels(predicted_class=predicted_class).inc()
    PREDICTION_CONFIDENCE.observe(confidence)

    return {
        "predicted_class": predicted_class,
        "confidence": confidence,
        "model_version": MODEL_VERSION,
    }
