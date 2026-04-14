"""
tests/integration/test_api.py — Integration tests para Preprocessing Service

🧒 PARA NIÑOS:
Comprobamos que el servicio de limpieza de datos
acepta flores válidas y rechaza medidas imposibles.

📘 TÉCNICO:
Tests de integración contra el Preprocessing Service.
Requiere el servicio corriendo (docker-compose.test.yml).
"""

import os

import httpx
import pytest

BASE_URL = os.getenv("PREPROCESSING_URL", "http://localhost:8001")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=30.0) as c:
        yield c


class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_structure(self, client):
        body = client.get("/health").json()
        assert body["status"] == "healthy"
        assert "service" in body


class TestPreprocess:
    def test_valid_iris_returns_200(self, client):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        response = client.post("/preprocess", json=payload)
        assert response.status_code == 200

    def test_preprocess_returns_features_array(self, client):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        body = client.post("/preprocess", json=payload).json()
        assert "features_array" in body
        assert len(body["features_array"]) == 4

    def test_preprocess_returns_validation_passed_true(self, client):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        body = client.post("/preprocess", json=payload).json()
        assert body["validation_passed"] is True

    def test_preprocess_features_array_preserves_order(self, client):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        body = client.post("/preprocess", json=payload).json()
        arr = body["features_array"]
        assert arr[0] == pytest.approx(5.1)
        assert arr[1] == pytest.approx(3.5)
        assert arr[2] == pytest.approx(1.4)
        assert arr[3] == pytest.approx(0.2)

    def test_negative_sepal_length_returns_422(self, client):
        payload = {"sepal_length": -1.0, "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        response = client.post("/preprocess", json=payload)
        assert response.status_code == 422

    def test_zero_petal_length_returns_422(self, client):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5, "petal_length": 0.0, "petal_width": 0.2}
        response = client.post("/preprocess", json=payload)
        assert response.status_code == 422

    def test_missing_field_returns_422(self, client):
        payload = {"sepal_length": 5.1, "sepal_width": 3.5}
        response = client.post("/preprocess", json=payload)
        assert response.status_code == 422

    def test_string_value_returns_422(self, client):
        payload = {"sepal_length": "cinco", "sepal_width": 3.5, "petal_length": 1.4, "petal_width": 0.2}
        response = client.post("/preprocess", json=payload)
        assert response.status_code == 422

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "preprocessing_requests_total" in response.text
