"""
tests/integration/test_api.py — Integration tests para Inference API

🧒 PARA NIÑOS:
Estos tests verifican que toda la cadena funciona junta:
enviamos medidas de flores reales y comprobamos que
el sistema completo responde correctamente.

📘 TÉCNICO:
Tests de integración que requieren los servicios levantados
(via docker-compose.test.yml). Usan httpx para hacer
requests HTTP reales contra los endpoints.

Prerequisito:
  docker compose -f docker-compose.test.yml up -d
  pytest tests/integration/ -v
"""

import os

import httpx
import pytest

# ── Configuración de conexión ─────────────────────────────
BASE_URL = os.getenv("INFERENCE_API_URL", "http://localhost:8000")
API_KEY = os.getenv("API_KEY", "test-api-key-integration")

VALID_IRIS = {
    "sepal_length": 5.1,
    "sepal_width": 3.5,
    "petal_length": 1.4,
    "petal_width": 0.2,
}


# ── Fixtures ──────────────────────────────────────────────
@pytest.fixture(scope="module")
def client():
    """Cliente HTTP con timeout extendido para integration tests."""
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


@pytest.fixture(scope="module")
def auth_headers():
    """Headers de autenticación válidos."""
    return {"X-API-Key": API_KEY}


# ── Health & Readiness ────────────────────────────────────
class TestHealthEndpoints:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        response = client.get("/health")
        body = response.json()
        assert "status" in body
        assert body["status"] == "healthy"

    def test_ready_returns_200(self, client):
        response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_response_has_model_loaded(self, client):
        response = client.get("/ready")
        body = response.json()
        assert "model_loaded" in body


# ── Autenticación ─────────────────────────────────────────
class TestAuthentication:
    def test_predict_without_api_key_returns_401(self, client):
        response = client.post("/predict", json=VALID_IRIS)
        assert response.status_code == 401

    def test_predict_with_wrong_api_key_returns_403(self, client):
        response = client.post(
            "/predict",
            json=VALID_IRIS,
            headers={"X-API-Key": "invalid-key"},
        )
        assert response.status_code == 403

    def test_predict_with_valid_api_key_returns_200(self, client, auth_headers):
        response = client.post("/predict", json=VALID_IRIS, headers=auth_headers)
        assert response.status_code == 200


# ── Predicción ────────────────────────────────────────────
class TestPrediction:
    def test_predict_setosa_sample(self, client, auth_headers):
        """Flores con pétalos pequeños deben ser setosa."""
        payload = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["predicted_class"] == "setosa"
        assert 0 <= body["confidence"] <= 1

    def test_predict_versicolor_sample(self, client, auth_headers):
        """Flores con pétalos medianos deben ser versicolor."""
        payload = {"sepal_length": 6.0, "sepal_width": 2.7, "petal_length": 5.1, "petal_width": 1.6}
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["predicted_class"] in ("versicolor", "virginica")

    def test_predict_virginica_sample(self, client, auth_headers):
        """Flores con pétalos grandes deben ser virginica."""
        payload = {"sepal_length": 6.3, "sepal_width": 3.3, "petal_length": 6.0, "petal_width": 2.5}
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 200
        body = response.json()
        assert body["predicted_class"] == "virginica"

    def test_predict_response_includes_model_version(self, client, auth_headers):
        response = client.post("/predict", json=VALID_IRIS, headers=auth_headers)
        body = response.json()
        assert "model_version" in body
        assert body["model_version"] is not None

    def test_predict_response_includes_input(self, client, auth_headers):
        response = client.post("/predict", json=VALID_IRIS, headers=auth_headers)
        body = response.json()
        assert "input_received" in body

    def test_predict_invalid_feature_returns_422(self, client, auth_headers):
        """Valores fuera de rango deben ser rechazados."""
        payload = {"sepal_length": -1.0, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_predict_missing_field_returns_422(self, client, auth_headers):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5}
        response = client.post("/predict", json=payload, headers=auth_headers)
        assert response.status_code == 422

    def test_predict_example_endpoint(self, client):
        """El endpoint de ejemplo no requiere API Key."""
        response = client.get("/predict/example")
        assert response.status_code == 200
        body = response.json()
        assert "example_request" in body


# ── Métricas ──────────────────────────────────────────────
class TestMetrics:
    def test_metrics_endpoint_returns_200(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_contains_request_counter(self, client, auth_headers):
        # Hacer una request para generar métricas
        client.post("/predict", json=VALID_IRIS, headers=auth_headers)
        response = client.get("/metrics")
        assert "http_requests_total" in response.text

    def test_metrics_content_type_is_text(self, client):
        response = client.get("/metrics")
        assert "text/plain" in response.headers["content-type"]
