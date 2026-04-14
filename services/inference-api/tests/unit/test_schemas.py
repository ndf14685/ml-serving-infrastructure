"""
test_schemas.py — Tests unitarios para los schemas Pydantic

🧒 PARA NIÑOS:
Estos tests comprueban que nuestros formularios (schemas)
funcionen bien: que acepten los datos correctos y
rechacen los incorrectos.
"""

import pytest
from pydantic import ValidationError

from app.models.schemas import PredictRequest, PredictResponse


class TestPredictRequest:
    """Tests para el schema de entrada PredictRequest"""

    def test_valid_request_creates_successfully(self):
        """
        🧒 Un formulario bien rellenado debe aceptarse sin problemas.
        """
        req = PredictRequest(
            sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
        )
        assert req.sepal_length == 5.1

    def test_negative_sepal_length_raises_error(self):
        """
        🧒 Un sépalo de longitud negativa no tiene sentido.
        Debe rechazarse.
        """
        with pytest.raises(ValidationError):
            PredictRequest(
                sepal_length=-1.0,  # ❌
                sepal_width=3.5,
                petal_length=1.4,
                petal_width=0.2,
            )

    def test_zero_petal_width_raises_error(self):
        """
        🧒 Un pétalo de ancho cero tampoco tiene sentido.
        """
        with pytest.raises(ValidationError):
            PredictRequest(
                sepal_length=5.1,
                sepal_width=3.5,
                petal_length=1.4,
                petal_width=0.0,  # ❌
            )

    def test_missing_field_raises_error(self):
        """
        🧒 Si falta un campo del formulario, se rechaza.
        """
        with pytest.raises(ValidationError):
            PredictRequest(
                sepal_length=5.1,
                sepal_width=3.5,
                # petal_length falta ❌
                petal_width=0.2,
            )

    def test_string_value_raises_error(self):
        """
        🧒 Si pones texto en vez de un número, se rechaza.
        """
        with pytest.raises(ValidationError):
            PredictRequest(
                sepal_length="largo",  # ❌
                sepal_width=3.5,
                petal_length=1.4,
                petal_width=0.2,
            )


class TestPredictResponse:
    """Tests para el schema de salida PredictResponse"""

    def test_valid_response_creates_successfully(self):
        """
        🧒 Una respuesta válida del modelo debe poder crearse sin problemas.
        """
        resp = PredictResponse(
            predicted_class="setosa",
            confidence=0.97,
            model_version="1.0.0",
            input_received={"sepal_length": 5.1},
        )
        assert resp.predicted_class == "setosa"
        assert resp.confidence == 0.97

    def test_confidence_above_one_raises_error(self):
        """
        🧒 La confianza no puede ser mayor al 100% (1.0).
        """
        with pytest.raises(ValidationError):
            PredictResponse(
                predicted_class="setosa",
                confidence=1.5,  # ❌ Mayor a 1.0
                model_version="1.0.0",
                input_received={},
            )

    def test_negative_confidence_raises_error(self):
        """
        🧒 La confianza no puede ser negativa.
        """
        with pytest.raises(ValidationError):
            PredictResponse(
                predicted_class="setosa",
                confidence=-0.1,  # ❌ Negativo
                model_version="1.0.0",
                input_received={},
            )
