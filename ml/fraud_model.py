
from pathlib import Path

import joblib
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
MODEL_PATH = ROOT / "ml" / "artifacts" / "fraud_pipeline.joblib"
METRICS_PATH = ROOT / "ml" / "model_metrics.json"

_model = joblib.load(MODEL_PATH)
_metrics = __import__("json").loads(METRICS_PATH.read_text())
FEATURE_NAMES = _metrics["feature_names"]


def predict_fraud(transaction_features: dict) -> dict:
    """Return fraud probability and risk level for one transaction."""
    missing = set(FEATURE_NAMES) - set(transaction_features)
    extra = set(transaction_features) - set(FEATURE_NAMES)

    if missing or extra:
        raise ValueError(
            f"Feature mismatch. Missing: {sorted(missing)}; "
            f"unexpected: {sorted(extra)}"
        )

    row = pd.DataFrame(
        [{name: transaction_features[name] for name in FEATURE_NAMES}]
    )

    if row.isnull().any().any():
        raise ValueError("Transaction features cannot contain null values.")

    probability = float(_model.predict_proba(row)[0, 1])

    if probability >= 0.5:
        risk_level = "high"
    elif probability >= 0.2:
        risk_level = "medium"
    else:
        risk_level = "low"

    return {
        "fraud_probability": probability,
        "risk_level": risk_level,
    }
