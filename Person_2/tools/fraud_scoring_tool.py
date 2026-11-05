"""
fraud_scoring_tool.py — Integration Adapter for Person 1's ML Fraud Model (Unit 1.C, 2.B)
Safely invokes Person 1's fraud prediction interface without fabricating scores when features are absent.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


def check_fraud_score(transaction: dict[str, Any]) -> dict[str, Any]:
    """
    Retrieve fraud probability and risk level from Person 1's model.
    Attempts:
      1. Direct in-process call to Person_1.serving.prediction_service.predict_fraud
      2. Feast online feature store lookup if model_features is null in ledger
      3. Fallback to unavailable without inventing scores.
    """
    features = transaction.get("model_features")
    tx_id = transaction.get("transaction_id")

    # If features are not directly attached, try Feast online feature store lookup
    if not isinstance(features, dict) and tx_id:
        try:
            from Person_1.feature_store.feature_pipeline import feast_store
            feast_pred = feast_store.predict_with_feast_features(tx_id)
            if feast_pred.get("fraud_probability") is not None:
                return {
                    "fraud_probability": feast_pred["fraud_probability"],
                    "risk_level": feast_pred["risk_level"],
                    "source": "feast_online_feature_store",
                    "error": None,
                }
        except Exception:
            pass

    if not isinstance(features, dict):
        return {
            "fraud_probability": None,
            "risk_level": "unavailable",
            "error": "Model features are not available for this transaction.",
        }

    try:
        try:
            from Person_1.serving.prediction_service import predict_fraud
        except ImportError:
            from ml.fraud_model import predict_fraud

        result = predict_fraud(features)
        return {
            "fraud_probability": result.get("fraud_probability"),
            "risk_level": result.get("risk_level", "unavailable"),
            "source": "person_1_ml_service",
            "error": None,
        }
    except Exception as exc:
        return {
            "fraud_probability": None,
            "risk_level": "unavailable",
            "error": f"Fraud assessment unavailable: {exc}",
        }
