"""
test_training.py — Tests for Training Pipeline, Evaluation Metrics, and Artifact Persistence
"""

import sys
from pathlib import Path
import json
from ml.models.registry import load_model, load_metrics, get_model_metadata


def test_model_artifact_loaded():
    model = load_model()
    assert hasattr(model, "predict_proba")
    assert hasattr(model, "predict")


def test_metrics_json_integrity():
    metrics = load_metrics()
    assert "selected_model" in metrics
    assert "models" in metrics
    assert "feature_names" in metrics
    assert len(metrics["feature_names"]) == 30
    assert "PR-AUC" in metrics["selection_metric"]


def test_model_metadata():
    meta = get_model_metadata()
    assert "model_name" in meta
    assert meta["feature_count"] == 30
    assert Path(meta["artifact_path"]).exists()
