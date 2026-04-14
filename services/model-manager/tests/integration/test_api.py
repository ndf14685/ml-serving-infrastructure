"""
tests/integration/test_api.py — Integration tests para Model Manager

🧒 PARA NIÑOS:
Verificamos que el servicio que guarda y gestiona
nuestro modelo responde correctamente a todas las preguntas.

📘 TÉCNICO:
Tests de integración contra el Model Manager Service.
Requiere el servicio corriendo (docker-compose.test.yml).
"""

import os

import httpx
import pytest

BASE_URL = os.getenv("MODEL_MANAGER_URL", "http://localhost:8002")


@pytest.fixture(scope="module")
def client():
    with httpx.Client(base_url=BASE_URL, timeout=60.0) as c:
        yield c


class TestHealth:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_response_is_healthy(self, client):
        body = response = client.get("/health").json()
        assert body["status"] == "healthy"

    def test_ready_returns_200(self, client):
        response = client.get("/ready")
        assert response.status_code == 200

    def test_ready_indicates_model_loaded(self, client):
        body = client.get("/ready").json()
        assert body.get("model_loaded") is True


class TestModelInfo:
    def test_model_info_returns_200(self, client):
        response = client.get("/model/info")
        assert response.status_code == 200

    def test_model_info_has_required_fields(self, client):
        body = client.get("/model/info").json()
        assert "version" in body
        assert "accuracy" in body
        assert "class_names" in body

    def test_model_info_class_names_are_iris_species(self, client):
        body = client.get("/model/info").json()
        expected = {"setosa", "versicolor", "virginica"}
        assert set(body["class_names"]) == expected

    def test_model_info_accuracy_is_reasonable(self, client):
        body = client.get("/model/info").json()
        assert 0.9 <= body["accuracy"] <= 1.0

    def test_model_version_endpoint(self, client):
        response = client.get("/model/version")
        assert response.status_code == 200
        body = response.json()
        assert "version" in body

    def test_metrics_endpoint(self, client):
        response = client.get("/metrics")
        assert response.status_code == 200
