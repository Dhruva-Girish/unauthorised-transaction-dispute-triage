"""
service.py — BentoML Model Serving Service (Unit 2.B)
Exposes the trained fraud detection model as an optimized BentoML cloud-native service.
"""

from __future__ import annotations

from typing import Any
import numpy as np

try:
    import bentoml
    BENTO_AVAILABLE = True
except ImportError:
    BENTO_AVAILABLE = False

from ml.models.registry import load_model, get_feature_names
from ml.serving.prediction_service import predict_fraud


if BENTO_AVAILABLE:
    @bentoml.service(
        name="fraud_detection_service",
        resources={"cpu": "2"},
        traffic={"timeout": 10},
    )
    class FraudDetectionBentoService:
        def __init__(self) -> None:
            self.model = load_model()
            self.feature_names = get_feature_names()

        @bentoml.api
        def predict(self, features: dict[str, float]) -> dict[str, Any]:
            """Real-time single transaction fraud prediction."""
            return predict_fraud(features)

        @bentoml.api
        def predict_batch(self, batch: list[dict[str, float]]) -> list[dict[str, Any]]:
            """Vectorized batch scoring endpoint."""
            return [predict_fraud(item) for item in batch]
else:
    class FraudDetectionBentoService:
        """Standalone mock/shim for BentoML service when bentoml is not installed."""
        def __init__(self) -> None:
            self.model = load_model()
            self.feature_names = get_feature_names()

        def predict(self, features: dict[str, float]) -> dict[str, Any]:
            return predict_fraud(features)

        def predict_batch(self, batch: list[dict[str, float]]) -> list[dict[str, Any]]:
            return [predict_fraud(item) for item in batch]


# Service instance for direct consumption
bento_service = FraudDetectionBentoService()
