"""
test_feature_store.py — Tests for Feast Feature Store Retrieval and Materialization (Unit 1.E)
"""

import sys
from pathlib import Path
import pytest
import pandas as pd
from ml.feature_store.feature_pipeline import feast_store


def test_materialization_and_online_retrieval():
    # Materialize features
    count = feast_store.materialize()
    assert count > 0

    # Retrieve online features for entity key
    results = feast_store.get_online_features([{"transaction_id": "TX1000"}])
    assert len(results) == 1
    features = results[0]
    assert features["transaction_id"] == "TX1000"
    assert "Amount" in features
    assert "Time" in features
    assert "V1" in features


def test_predict_with_feast_features():
    # Directly score using Feast online store features
    prediction = feast_store.predict_with_feast_features("TX1000")
    assert prediction["transaction_id"] == "TX1000"
    assert "fraud_probability" in prediction
    assert prediction["risk_level"] in {"low", "medium", "high"}
    assert prediction["source"] == "feast_online_store"


def test_offline_historical_feature_retrieval():
    entity_df = pd.DataFrame([{"transaction_id": "TX1000"}])
    historical = feast_store.get_historical_features(entity_df)
    assert len(historical) == 1
    assert "Amount" in historical.columns
    assert "Class" in historical.columns
