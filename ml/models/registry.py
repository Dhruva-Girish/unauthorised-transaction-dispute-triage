"""
registry.py — Model Artifact Registry and Loader
Provides thread-safe model artifact loading, versioning metadata, and feature validation.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any
import joblib

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "artifacts" / "fraud_pipeline.joblib"
METRICS_PATH = ROOT / "model_metrics.json"

_cached_model = None
_cached_metrics = None


def load_model() -> Any:
    """Load serialized model pipeline with caching."""
    global _cached_model
    if _cached_model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model artifact not found at {MODEL_PATH}")
        _cached_model = joblib.load(MODEL_PATH)
    return _cached_model


def load_metrics() -> dict[str, Any]:
    """Load model evaluation metadata and feature definitions."""
    global _cached_metrics
    if _cached_metrics is None:
        if not METRICS_PATH.exists():
            raise FileNotFoundError(f"Metrics metadata not found at {METRICS_PATH}")
        _cached_metrics = json.loads(METRICS_PATH.read_text(encoding="utf-8"))
    return _cached_metrics


def get_feature_names() -> list[str]:
    """Return required feature vector names in canonical order."""
    metrics = load_metrics()
    return metrics.get("feature_names", ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"])


def get_model_metadata() -> dict[str, Any]:
    """Return operational metadata about the current production model."""
    metrics = load_metrics()
    return {
        "model_name": metrics.get("selected_model", "fraud_pipeline"),
        "selection_metric": metrics.get("selection_metric", "PR-AUC"),
        "selected_threshold": metrics.get("selected_threshold", 0.5),
        "feature_count": len(get_feature_names()),
        "artifact_path": str(MODEL_PATH),
    }
