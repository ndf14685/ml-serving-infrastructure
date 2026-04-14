"""
test_validators.py — Tests unitarios para validación de features

🧒 PARA NIÑOS:
Antes de darle medidas de flores a nuestra máquina mágica,
tenemos que verificar que las medidas tengan sentido.
¡Una flor no puede tener pétalos de 100 metros!
Estos tests comprueban que nuestra policía de medidas
(validators.py) hace bien su trabajo.

📘 TDD: Tests escritos ANTES de validators.py.
Ciclo: RED (falla) → GREEN (implementar) → REFACTOR.
"""

import pytest

from app.validators import (
    FEATURE_RANGES,
    IrisFeatures,
    ValidationError,
    validate_iris_features,
)


# ── TESTS DE validate_iris_features() ────────────────────────


class TestValidateIrisFeatures:
    """Tests para la función validate_iris_features()"""

    def test_valid_features_pass_validation(self):
        """
        🧒 Si le damos medidas de flores reales y posibles,
        la validación debe decir que todo está bien.
        """
        valid_input = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        result = validate_iris_features(valid_input)
        assert result is not None
        assert isinstance(result, IrisFeatures)

    def test_negative_values_raise_validation_error(self):
        """
        🧒 Las flores no tienen medidas negativas.
        Si alguien nos dice que el pétalo mide -1 cm,
        debemos rechazarlo.
        """
        invalid_input = {
            "sepal_length": -1.0,  # ❌ Negativo
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        with pytest.raises(ValidationError, match="sepal_length"):
            validate_iris_features(invalid_input)

    def test_zero_values_raise_validation_error(self):
        """
        🧒 Una flor con sépalos de tamaño cero no existe.
        Valores de cero son inválidos para las medidas.
        """
        invalid_input = {
            "sepal_length": 0.0,  # ❌ Cero
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        with pytest.raises(ValidationError, match="sepal_length"):
            validate_iris_features(invalid_input)

    def test_values_above_max_raise_validation_error(self):
        """
        🧒 Las flores Iris tienen límites de tamaño.
        Si alguien pone un sépalo de 100 cm, algo está mal.
        """
        invalid_input = {
            "sepal_length": 100.0,  # ❌ Demasiado grande
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        with pytest.raises(ValidationError, match="sepal_length"):
            validate_iris_features(invalid_input)

    def test_missing_feature_raises_validation_error(self):
        """
        🧒 Si faltan datos (como no poner el ancho del sépalo),
        debemos rechazarlo porque el modelo necesita los 4 datos.
        """
        incomplete_input = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            # petal_length falta ❌
            "petal_width": 0.2,
        }
        with pytest.raises((ValidationError, KeyError)):
            validate_iris_features(incomplete_input)

    def test_non_numeric_values_raise_validation_error(self):
        """
        🧒 Si alguien escribe "grande" en vez de un número,
        debemos rechazarlo porque necesitamos números.
        """
        invalid_input = {
            "sepal_length": "grande",  # ❌ No es un número
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        with pytest.raises((ValidationError, ValueError)):
            validate_iris_features(invalid_input)

    def test_boundary_values_are_valid(self):
        """
        🧒 Los valores exactamente en el límite (como el
        valor mínimo o máximo permitido) deben ser aceptados.
        """
        # Usar los valores límite exactos del dataset Iris
        boundary_input = {
            "sepal_length": FEATURE_RANGES["sepal_length"]["min"],
            "sepal_width": FEATURE_RANGES["sepal_width"]["min"],
            "petal_length": FEATURE_RANGES["petal_length"]["min"],
            "petal_width": FEATURE_RANGES["petal_width"]["min"],
        }
        result = validate_iris_features(boundary_input)
        assert result is not None

    def test_all_features_validated_independently(self):
        """
        🧒 Cada medida se revisa por separado. Si el sépalo
        está mal Y el pétalo está mal, el error nos dice
        cuál fue el primer problema.
        """
        invalid_input = {
            "sepal_length": -5.0,  # ❌
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        with pytest.raises(ValidationError):
            validate_iris_features(invalid_input)


# ── TESTS DE IrisFeatures (Pydantic model) ───────────────────


class TestIrisFeatures:
    """Tests para el modelo Pydantic IrisFeatures"""

    def test_iris_features_creates_from_dict(self):
        """
        🧒 Verifica que podemos crear un objeto de medidas
        de flor a partir de un diccionario.
        """
        data = {
            "sepal_length": 5.1,
            "sepal_width": 3.5,
            "petal_length": 1.4,
            "petal_width": 0.2,
        }
        features = IrisFeatures(**data)
        assert features.sepal_length == 5.1
        assert features.sepal_width == 3.5
        assert features.petal_length == 1.4
        assert features.petal_width == 0.2

    def test_iris_features_to_list(self):
        """
        🧒 Verifica que podemos convertir las medidas en
        una lista de números ordenada, que es lo que
        necesita el modelo de ML.
        """
        features = IrisFeatures(
            sepal_length=5.1, sepal_width=3.5, petal_length=1.4, petal_width=0.2
        )
        feature_list = features.to_list()
        assert feature_list == [5.1, 3.5, 1.4, 0.2]
        assert len(feature_list) == 4
