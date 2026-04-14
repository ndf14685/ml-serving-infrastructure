"""
middleware/metrics.py — Instrumentación Prometheus

🧒 PARA NIÑOS:
Imagina que tenemos un contador en la puerta del club que
cuenta cuántas personas entran, cuánto tiempo tardan en
hacer su pedido y si hay algún problema. Eso son las métricas:
números que nos dicen cómo está funcionando nuestro servicio.

📘 TÉCNICO:
Define y exporta las métricas Prometheus para la Inference API.
Usa prometheus_client con labels para segmentar por endpoint,
método HTTP y código de respuesta.
"""

from prometheus_client import Counter, Gauge, Histogram

# ── Contadores ───────────────────────────────────────────────

REQUEST_COUNT = Counter(
    name="inference_api_requests_total",
    documentation="Número total de requests recibidos por la API",
    labelnames=["method", "endpoint", "http_status"],
)

PREDICTION_COUNT = Counter(
    name="inference_api_predictions_total",
    documentation="Número total de predicciones realizadas por clase",
    labelnames=["predicted_class"],
)

# ── Histogramas (distribuciones) ─────────────────────────────

REQUEST_DURATION = Histogram(
    name="inference_api_request_duration_seconds",
    documentation="Duración de los requests en segundos",
    labelnames=["method", "endpoint"],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0],
)

PREDICTION_CONFIDENCE = Histogram(
    name="inference_api_prediction_confidence",
    documentation="Distribución de scores de confianza del modelo",
    buckets=[0.5, 0.6, 0.7, 0.8, 0.85, 0.9, 0.95, 0.99, 1.0],
)

# ── Gauges (valores actuales) ────────────────────────────────

MODEL_LOADED = Gauge(
    name="inference_api_model_loaded",
    documentation="1 si el modelo está cargado en memoria, 0 si no",
)
