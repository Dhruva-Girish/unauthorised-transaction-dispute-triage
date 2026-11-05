"""
evaluate_model.py — Offline Model Evaluation and Threshold Analysis (Unit 1.F)
Calculates PR-AUC, ROC-AUC, threshold-tuning trade-offs, and operational error rates.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from sklearn.metrics import (
    precision_recall_curve,
    roc_curve,
    average_precision_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

try:
    from ml.models.registry import load_model, get_feature_names
except ImportError:
    from ml.models.registry import load_model, get_feature_names


def evaluate_dataset(test_csv_path: Path | str | None = None) -> dict[str, Any]:
    """
    Run detailed evaluation on a test dataset across operating thresholds (0.1 to 0.9).
    """
    path = Path(test_csv_path) if test_csv_path else ROOT / "data" / "creditcard_sample.csv"
    if not path.exists():
        raise FileNotFoundError(f"Test dataset not found at {path}")

    df = pd.read_csv(path)
    feature_names = get_feature_names()
    X = df[feature_names]
    y_true = df["Class"].astype(int)

    model = load_model()
    probabilities = model.predict_proba(X)[:, 1]

    pr_auc = float(average_precision_score(y_true, probabilities))
    roc_auc = float(roc_auc_score(y_true, probabilities))

    # Evaluate multiple decision thresholds
    thresholds = [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]
    threshold_metrics = []

    for th in thresholds:
        preds = (probabilities >= th).astype(int)
        cm = confusion_matrix(y_true, preds).tolist()
        tn, fp, fn, tp = cm[0][0], cm[0][1], cm[1][0], cm[1][1]
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        threshold_metrics.append({
            "threshold": th,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "false_positive_rate": round(fp / (tn + fp) if (tn + fp) > 0 else 0.0, 4),
            "confusion_matrix": {"tn": tn, "fp": fp, "fn": fn, "tp": tp},
        })

    return {
        "dataset": path.name,
        "sample_count": len(df),
        "fraud_count": int(y_true.sum()),
        "pr_auc": round(pr_auc, 4),
        "roc_auc": round(roc_auc, 4),
        "threshold_analysis": threshold_metrics,
        "optimal_threshold_recommendation": 0.5,
    }


if __name__ == "__main__":
    report = evaluate_dataset()
    print(json.dumps(report, indent=2))
