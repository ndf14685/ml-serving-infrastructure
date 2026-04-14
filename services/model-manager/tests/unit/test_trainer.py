"""
test_trainer.py — Tests unitarios para el módulo trainer

🧒 PARA NIÑOS:
Estos son los "exámenes" para comprobar que nuestro
maestro (trainer.py) hace bien su trabajo. Cada test
es una pregunta diferente que le hacemos para ver si
la respuesta es correcta.

📘 TDD: Estos tests se escriben ANTES del código de
producción. Primero falla (RED), luego se implementa
el código mínimo para que pase (GREEN), luego se mejora
sin romper los tests (REFACTOR).
"""

import os
import tempfile
from pathlib import Path

import pytest

# Importamos las funciones que vamos a testear
from app.trainer import (
    IRIS_CLASS_NAMES,
    MODEL_VERSION,
    get_model_metadata,
    load_model,
    train_model,
)


# ── FIXTURES ────────────────────────────────────────────────


@pytest.fixture
def temp_model_path(tmp_path):
    """
    🧒 PARA NIÑOS: Esta es una carpeta temporal que se crea
    solo para hacer las pruebas y se borra sola cuando
    terminamos. ¡Como una hoja de borrador!

    📘 Genera una ruta temporal única para cada test,
    asegurando aislamiento entre pruebas.
    """
    return str(tmp_path / "test_model.pkl")


@pytest.fixture
def trained_model_path(temp_model_path):
    """
    🧒 PARA NIÑOS: Esta preparación entrena un modelo
    de prueba para que los tests que lo necesiten
    ya lo tengan listo.

    📘 Entrena y guarda un modelo real en una ruta temporal.
    Fixture de setup para tests que necesitan un modelo existente.
    """
    train_model(temp_model_path)
    return temp_model_path


# ── TESTS DE train_model() ───────────────────────────────────


class TestTrainModel:
    """Tests para la función train_model()"""

    def test_train_model_creates_file(self, temp_model_path):
        """
        🧒 Verifica que después de entrenar, el archivo del
        modelo realmente exista en el disco.
        """
        train_model(temp_model_path)
        assert Path(temp_model_path).exists(), "El archivo del modelo debe existir después del entrenamiento"

    def test_train_model_returns_dict(self, temp_model_path):
        """
        🧒 Verifica que train_model devuelva un diccionario
        con información sobre el entrenamiento.
        """
        result = train_model(temp_model_path)
        assert isinstance(result, dict), "train_model debe retornar un diccionario"

    def test_train_model_returns_accuracy(self, temp_model_path):
        """
        🧒 Verifica que el modelo aprenda bien: al menos
        el 90% de las flores debe identificar correctamente.
        """
        result = train_model(temp_model_path)
        assert "accuracy" in result, "El resultado debe incluir 'accuracy'"
        assert result["accuracy"] >= 0.90, (
            f"Accuracy {result['accuracy']:.2f} debe ser >= 0.90 para el dataset Iris"
        )

    def test_train_model_returns_version(self, temp_model_path):
        """
        🧒 Verifica que el modelo tenga un número de versión
        para saber cuál estamos usando.
        """
        result = train_model(temp_model_path)
        assert result["version"] == MODEL_VERSION

    def test_train_model_returns_class_names(self, temp_model_path):
        """
        🧒 Verifica que el modelo conozca los nombres de
        los tres tipos de flores Iris.
        """
        result = train_model(temp_model_path)
        assert result["class_names"] == IRIS_CLASS_NAMES
        assert result["n_classes"] == 3

    def test_train_model_creates_parent_directories(self, tmp_path):
        """
        🧒 Verifica que si la carpeta donde queremos guardar
        el modelo no existe, se crea automáticamente.
        """
        deep_path = str(tmp_path / "deep" / "nested" / "model.pkl")
        train_model(deep_path)
        assert Path(deep_path).exists()

    def test_train_model_raises_on_empty_path(self):
        """
        🧒 Verifica que si le damos una ruta vacía,
        nos avisa con un error claro.
        """
        with pytest.raises(ValueError, match="model_path no puede estar vacío"):
            train_model("")

    def test_train_model_is_reproducible(self, tmp_path):
        """
        🧒 Verifica que si entrenamos el modelo dos veces
        con los mismos parámetros, obtenemos el mismo resultado.
        Importante para debugging y reproducibilidad.
        """
        path1 = str(tmp_path / "model1.pkl")
        path2 = str(tmp_path / "model2.pkl")

        result1 = train_model(path1, random_state=42)
        result2 = train_model(path2, random_state=42)

        assert result1["accuracy"] == result2["accuracy"], (
            "El entrenamiento debe ser determinístico con el mismo random_state"
        )


# ── TESTS DE load_model() ────────────────────────────────────


class TestLoadModel:
    """Tests para la función load_model()"""

    def test_load_model_returns_pipeline(self, trained_model_path):
        """
        🧒 Verifica que podemos sacar el modelo de la caja
        y que está listo para usarse.
        """
        from sklearn.pipeline import Pipeline

        model = load_model(trained_model_path)
        assert model is not None
        assert isinstance(model, Pipeline)

    def test_load_model_returns_none_if_not_found(self, tmp_path):
        """
        🧒 Verifica que si el modelo no existe, nos dice
        que no lo encontró (en vez de explotar con un error).
        """
        model = load_model(str(tmp_path / "no_existe.pkl"))
        assert model is None

    def test_loaded_model_can_predict(self, trained_model_path):
        """
        🧒 Verifica que el modelo que cargamos realmente
        puede hacer predicciones sobre flores.
        """
        import numpy as np

        model = load_model(trained_model_path)
        # Features de una flor Iris setosa típica
        sample = np.array([[5.1, 3.5, 1.4, 0.2]])
        prediction = model.predict(sample)
        assert prediction[0] in [0, 1, 2], "La predicción debe ser una clase válida (0, 1 o 2)"


# ── TESTS DE get_model_metadata() ────────────────────────────


class TestGetModelMetadata:
    """Tests para la función get_model_metadata()"""

    def test_metadata_shows_available_when_model_exists(self, trained_model_path):
        """
        🧒 Verifica que cuando el modelo existe, nos dice
        que está disponible para usar.
        """
        metadata = get_model_metadata(trained_model_path)
        assert metadata["status"] == "available"

    def test_metadata_shows_not_found_when_missing(self, tmp_path):
        """
        🧒 Verifica que cuando el modelo no existe, nos
        dice que no está disponible.
        """
        metadata = get_model_metadata(str(tmp_path / "phantom.pkl"))
        assert metadata["status"] == "not_found"

    def test_metadata_includes_version(self, trained_model_path):
        """
        🧒 Verifica que los metadatos incluyan la versión
        del modelo.
        """
        metadata = get_model_metadata(trained_model_path)
        assert metadata["version"] == MODEL_VERSION

    def test_metadata_includes_class_names(self, trained_model_path):
        """
        🧒 Verifica que los metadatos incluyan los nombres
        de las flores que el modelo puede identificar.
        """
        metadata = get_model_metadata(trained_model_path)
        assert metadata["class_names"] == IRIS_CLASS_NAMES

    def test_metadata_includes_feature_names(self, trained_model_path):
        """
        🧒 Verifica que los metadatos incluyan los nombres
        de las medidas de la flor que necesita el modelo.
        """
        metadata = get_model_metadata(trained_model_path)
        assert len(metadata["feature_names"]) == 4

    def test_metadata_file_size_is_positive(self, trained_model_path):
        """
        🧒 Verifica que el archivo del modelo tenga un
        tamaño mayor a cero (que no esté vacío).
        """
        metadata = get_model_metadata(trained_model_path)
        assert metadata["file_size_bytes"] > 0
