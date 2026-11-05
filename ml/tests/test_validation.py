"""
test_validation.py — Tests for Data Ingestion Validation and Schema Consistency (Unit 1.D)
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
from ml.preprocessing.data_validator import validate_feature_vector, validate_ingestion_data, REQUIRED_FEATURES


def test_valid_feature_vector():
    features = {name: 0.0 for name in REQUIRED_FEATURES}
    features["Amount"] = 150.0
    is_valid, errors = validate_feature_vector(features)
    assert is_valid is True
    assert len(errors) == 0


def test_missing_feature_rejected():
    features = {name: 0.0 for name in REQUIRED_FEATURES}
    del features["V1"]
    is_valid, errors = validate_feature_vector(features)
    assert is_valid is False
    assert any("V1" in err for err in errors)


def test_extra_feature_rejected():
    features = {name: 0.0 for name in REQUIRED_FEATURES}
    features["malicious_extra"] = 999.0
    is_valid, errors = validate_feature_vector(features)
    assert is_valid is False
    assert any("malicious_extra" in err for err in errors)


def test_negative_amount_rejected():
    features = {name: 0.0 for name in REQUIRED_FEATURES}
    features["Amount"] = -50.0
    is_valid, errors = validate_feature_vector(features)
    assert is_valid is False
    assert any("negative" in err for err in errors)


def test_null_value_rejected():
    features = {name: 0.0 for name in REQUIRED_FEATURES}
    features["V10"] = None
    is_valid, errors = validate_feature_vector(features)
    assert is_valid is False
    assert any("null" in err for err in errors)


def test_ingestion_batch_validation():
    data = {name: [0.0, 1.0] for name in REQUIRED_FEATURES}
    data["Class"] = [0, 1]
    df = pd.DataFrame(data)
    res = validate_ingestion_data(df, is_training=True)
    assert res["is_valid"] is True
    assert res["row_count"] == 2
