"""
trainer.py — Entrenamiento y serialización del modelo ML

🧒 PARA NIÑOS:
Imagina que tienes un libro mágico que aprende a reconocer
flores mirando fotos. Este archivo es el que le enseña al
libro: le muestra muchas flores con sus medidas y sus nombres,
y el libro aprende solo. Cuando ya aprendió, lo guardamos
en una caja (archivo .pkl) para usarlo después sin tener
que enseñarle de nuevo.

📘 TÉCNICO:
Entrena un clasificador RandomForest con el dataset Iris de
scikit-learn y serializa el modelo + el scaler en disco
usando joblib. Expone métricas de entrenamiento para validación.
"""

import logging
from pathlib import Path
from typing import Optional

import joblib
import numpy as np
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, classification_report

logger = logging.getLogger(__name__)

# Nombres de las clases del dataset Iris
IRIS_CLASS_NAMES = ["setosa", "versicolor", "virginica"]

# Versión del modelo actual
MODEL_VERSION = "1.0.0"


def train_model(model_path: str, random_state: int = 42) -> dict:
    """
    🧒 PARA NIÑOS:
    Esta función es como un maestro que enseña a la máquina
    a reconocer flores. Le da muchos ejemplos de flores con
    sus medidas y le dice qué tipo es cada una. La máquina
    aprende y luego la guardamos para usarla después.

    📘 TÉCNICO:
    Carga el dataset Iris, divide en train/test (80/20),
    crea un Pipeline de sklearn (StandardScaler + RandomForest),
    lo entrena, evalúa y serializa en la ruta indicada.

    Args:
        model_path (str): Ruta donde guardar el modelo serializado.
        random_state (int): Semilla para reproducibilidad. Default: 42.

    Returns:
        dict: Métricas de entrenamiento:
              {'accuracy': float, 'version': str, 'n_classes': int,
               'class_names': list, 'model_path': str}

    Raises:
        ValueError: Si model_path está vacío o es inválido.
        IOError: Si no se puede escribir el archivo del modelo.
    """
    if not model_path:
        raise ValueError("model_path no puede estar vacío")

    logger.info("Iniciando entrenamiento del modelo Iris v%s", MODEL_VERSION)

    # Carga el dataset Iris (150 muestras, 4 features, 3 clases)
    iris = load_iris()
    X, y = iris.data, iris.target

    # Divide en 80% entrenamiento y 20% evaluación
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    # Pipeline: primero escala los datos, luego clasifica
    pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),  # Normaliza features a media=0, std=1
            (
                "classifier",
                RandomForestClassifier(
                    n_estimators=100,
                    random_state=random_state,
                    class_weight="balanced",  # Maneja desbalance de clases
                ),
            ),
        ]
    )

    # Entrena el modelo con los datos de entrenamiento
    pipeline.fit(X_train, y_train)

    # Evalúa el modelo con datos que nunca vio durante el entrenamiento
    y_pred = pipeline.predict(X_test)
    accuracy = float(accuracy_score(y_test, y_pred))

    logger.info("Accuracy del modelo: %.4f", accuracy)
    logger.info("\n%s", classification_report(y_test, y_pred, target_names=IRIS_CLASS_NAMES))

    # Guarda el modelo en disco
    model_file = Path(model_path)
    model_file.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_file)

    logger.info("Modelo guardado en: %s", model_path)

    return {
        "accuracy": accuracy,
        "version": MODEL_VERSION,
        "n_classes": len(IRIS_CLASS_NAMES),
        "class_names": IRIS_CLASS_NAMES,
        "model_path": str(model_path),
        "n_features": X.shape[1],
        "feature_names": list(iris.feature_names),
    }


def load_model(model_path: str) -> Optional[Pipeline]:
    """
    🧒 PARA NIÑOS:
    Esta función abre la caja donde guardamos el modelo
    aprendido y lo saca para poder usarlo. Es como abrir
    una caja de herramientas para usar las herramientas
    que guardaste antes.

    📘 TÉCNICO:
    Deserializa y retorna el Pipeline sklearn desde un archivo
    joblib. Retorna None si el archivo no existe.

    Args:
        model_path (str): Ruta al archivo .pkl del modelo.

    Returns:
        Pipeline | None: Pipeline sklearn listo para predict(),
                         o None si el archivo no existe.

    Raises:
        IOError: Si el archivo existe pero está corrupto.
    """
    model_file = Path(model_path)

    if not model_file.exists():
        logger.warning("Archivo de modelo no encontrado: %s", model_path)
        return None

    logger.info("Cargando modelo desde: %s", model_path)
    pipeline = joblib.load(model_file)
    logger.info("Modelo cargado exitosamente")

    return pipeline


def get_model_metadata(model_path: str) -> dict:
    """
    🧒 PARA NIÑOS:
    Esta función lee la etiqueta de nuestra caja mágica y
    nos dice qué hay adentro: qué versión es, cuándo se
    hizo y qué tan bueno es el modelo.

    📘 TÉCNICO:
    Retorna un diccionario con metadatos del modelo:
    versión, estado de carga, features esperadas y clases.
    No carga el modelo completo en memoria si ya está cargado.

    Args:
        model_path (str): Ruta al archivo .pkl del modelo.

    Returns:
        dict: Metadatos del modelo con campos version, status,
              class_names, feature_names, model_path.
    """
    model_file = Path(model_path)
    is_available = model_file.exists()

    return {
        "version": MODEL_VERSION,
        "status": "available" if is_available else "not_found",
        "class_names": IRIS_CLASS_NAMES,
        "feature_names": [
            "sepal length (cm)",
            "sepal width (cm)",
            "petal length (cm)",
            "petal width (cm)",
        ],
        "model_path": str(model_path),
        "file_size_bytes": model_file.stat().st_size if is_available else 0,
    }
