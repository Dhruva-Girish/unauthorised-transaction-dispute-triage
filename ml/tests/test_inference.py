"""
test_inference.py — Tests for Online & Batch Inference, Caching, and Prediction Interface
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
from ml.serving.prediction_service import predict_fraud, _cache
from ml.serving.batch_inference import score_batch
from ml.models.registry import get_feature_names


def get_sample_features():
    names = get_feature_names()
    return {name: 0.0 for name in names}


def test_predict_fraud_valid_contract():
    features = get_sample_features()
    result = predict_fraud(features)

    assert "fraud_probability" in result
    assert "risk_level" in result
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert result["risk_level"] in {"low", "medium", "high"}
    assert "inference_latency_ms" in result


def test_predict_fraud_caching():
    features = get_sample_features()
    features["Amount"] = 42.0

    res1 = predict_fraud(features, use_cache=True)
    res2 = predict_fraud(features, use_cache=True)

    assert res2.get("cached") is True
    assert res1["fraud_probability"] == res2["fraud_probability"]


def test_batch_scoring():
    features = get_sample_features()
    df = pd.DataFrame([features for _ in range(10)])
    result = score_batch(df)

    assert result["status"] == "COMPLETED"
    assert result["total_records_scored"] == 10
    assert "risk_breakdown" in result
    assert result["throughput_records_per_sec"] > 0
