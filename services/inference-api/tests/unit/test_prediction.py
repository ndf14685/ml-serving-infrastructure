"""
test_prediction.py — Tests unitarios para el servicio de predicción

🧒 PARA NIÑOS:
Probamos que la función que hace las predicciones funcione bien
en distintas situaciones: con datos buenos, con datos malos,
y con un modelo que funciona como esperamos.

📘 TDD: Estos tests guían la implementación de prediction.py
"""

from unittest.mock import MagicMock

import numpy as np
import pytest

from app.services.prediction import IRIS_CLASS_NAMES, run_prediction


# ── FIXTURES ────────────────────────────────────────────────

@pytest.fixture
def mock_model():
    """
    🧒 PARA NIÑOS:
    Un modelo falso que simula lo que haría el modelo real.
    Lo usamos en los tests para no tener que entrenar un
    modelo real cada vez (sería muy lento).

    📘 TÉCNICO:
    MagicMock que simula un Pipeline sklearn.
    predict_proba retorna probabilidades donde setosa tiene 0.97.
    """
    model = MagicMock()
    # Simular que predice setosa con 97% de confianza
    model.predict_proba.return_value = np.array([[0.97, 0.02, 0.01]])
    return model


@pytest.fixture
def valid_features():
    """
    🧒 PARA NIÑOS:
    Medidas de una flor Iris setosa típica para usar en tests.
    """
    return [5.1, 3.5, 1.4, 0.2]


# ── TESTS ────────────────────────────────────────────────────

class TestRunPrediction:
    """Tests para la función run_prediction()"""

    def test_returns_predicted_class(self, mock_model, valid_features):
        """
        🧒 La predicción debe decirnos el nombre del tipo de flor.
        """
        result = run_prediction(mock_model, valid_features)
        assert "predicted_class" in result
        assert result["predicted_class"] in IRIS_CLASS_NAMES

    def test_returns_confidence_score(self, mock_model, valid_features):
        """
        🧒 La predicción debe incluir un número que diga qué tan
        segura está la máquina (entre 0 y 1).
        """
        result = run_prediction(mock_model, valid_features)
        assert "confidence" in result
        assert 0.0 <= result["confidence"] <= 1.0

    def test_returns_model_version(self, mock_model, valid_features):
        """
        🧒 La predicción debe incluir la versión del modelo
        que la realizó, para saber de dónde vino.
        """
        result = run_prediction(mock_model, valid_features)
        assert "model_version" in result
        assert result["model_version"] is not None

    def test_setosa_predicted_correctly(self, mock_model, valid_features):
        """
        🧒 Con el modelo que configuramos (97% setosa),
        debe predecir setosa.
        """
        result = run_prediction(mock_model, valid_features)
        assert result["predicted_class"] == "setosa"
        assert result["confidence"] == pytest.approx(0.97)

    def test_versicolor_predicted_correctly(self, valid_features):
        """
        🧒 Si el modelo está más seguro de que es versicolor,
        debe predecir versicolor.
        """
        model = MagicMock()
        model.predict_proba.return_value = np.array([[0.05, 0.90, 0.05]])

        result = run_prediction(model, valid_features)
        assert result["predicted_class"] == "versicolor"

    def test_wrong_number_of_features_raises_error(self, mock_model):
        """
        🧒 Si le damos 3 medidas en vez de 4, debe quejarse.
        El modelo necesita exactamente 4 medidas.
        """
        with pytest.raises(ValueError, match="4 features"):
            run_prediction(mock_model, [5.1, 3.5, 1.4])  # ❌ Solo 3

    def test_model_is_called_with_correct_shape(self, mock_model, valid_features):
        """
        🧒 Verifica que le pasamos los datos al modelo en el
        formato correcto (como una tabla de 1 fila y 4 columnas).
        """
        run_prediction(mock_model, valid_features)

        # Verificar que predict_proba fue llamado con la forma correcta
        call_args = mock_model.predict_proba.call_args[0][0]
        assert call_args.shape == (1, 4), "Los features deben tener forma (1, 4)"

    def test_model_exception_raises_runtime_error(self, valid_features):
        """
        🧒 Si la máquina mágica falla por alguna razón,
        debemos atrapar ese error y dar un mensaje claro.
        """
        broken_model = MagicMock()
        broken_model.predict_proba.side_effect = Exception("Model exploded!")

        with pytest.raises(RuntimeError, match="Error durante la inferencia"):
            run_prediction(broken_model, valid_features)
