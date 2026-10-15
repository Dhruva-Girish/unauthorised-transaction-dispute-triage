
import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    classification_report,
    confusion_matrix,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "creditcard.csv"
ARTIFACT_DIR = ROOT / "ml" / "artifacts"
METRICS_PATH = ROOT / "ml" / "model_metrics.json"

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "Class"


def main():
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH)
    X = df.drop(columns=[TARGET])
    y = df[TARGET].astype(int)

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=TEST_SIZE,
        random_state=RANDOM_STATE,
        stratify=y,
    )

    models = {
        "logistic_regression": Pipeline([
            ("scaler", StandardScaler()),
            ("classifier", LogisticRegression(
                class_weight="balanced",
                max_iter=2000,
                random_state=RANDOM_STATE,
            )),
        ]),
        "random_forest": RandomForestClassifier(
            n_estimators=200,
            class_weight="balanced",
            random_state=RANDOM_STATE,
            n_jobs=-1,
        ),
    }

    results = {}
    best_name = None
    best_model = None
    best_pr_auc = -1.0

    for name, model in models.items():
        print(f"\nTraining {name}...")
        model.fit(X_train, y_train)

        probabilities = model.predict_proba(X_test)[:, 1]
        predictions = (probabilities >= 0.5).astype(int)

        pr_auc = average_precision_score(y_test, probabilities)
        results[name] = {
            "precision": float(precision_score(
                y_test, predictions, zero_division=0
            )),
            "recall": float(recall_score(
                y_test, predictions, zero_division=0
            )),
            "f1_score": float(f1_score(
                y_test, predictions, zero_division=0
            )),
            "pr_auc": float(pr_auc),
            "roc_auc": float(roc_auc_score(y_test, probabilities)),
            "threshold": 0.5,
            "confusion_matrix": confusion_matrix(
                y_test, predictions
            ).tolist(),
            "classification_report": classification_report(
                y_test, predictions, output_dict=True, zero_division=0
            ),
        }

        print(f"PR-AUC: {pr_auc:.4f}")
        print(f"Precision: {results[name]['precision']:.4f}")
        print(f"Recall: {results[name]['recall']:.4f}")

        if pr_auc > best_pr_auc:
            best_pr_auc = pr_auc
            best_name = name
            best_model = model

    joblib.dump(best_model, ARTIFACT_DIR / "fraud_pipeline.joblib")

    metrics = {
        "dataset": "Credit Card Fraud Detection",
        "target": TARGET,
        "positive_class": 1,
        "random_state": RANDOM_STATE,
        "test_size": TEST_SIZE,
        "selection_metric": "PR-AUC",
        "selected_model": best_name,
        "selected_threshold": 0.5,
        "models": results,
        "feature_names": X.columns.tolist(),
        "note": (
            "Threshold 0.5 is an initial default, not an optimized "
            "operating threshold. Select a deployment threshold using "
            "validation data and operational requirements."
        ),
    }

    METRICS_PATH.write_text(json.dumps(metrics, indent=2))

    print(f"\nSelected model: {best_name}")
    print(f"Saved model to: {ARTIFACT_DIR / 'fraud_pipeline.joblib'}")
    print(f"Saved metrics to: {METRICS_PATH}")


if __name__ == "__main__":
    main()
