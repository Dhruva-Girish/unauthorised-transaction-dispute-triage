"""
batch_inference.py — Batch Scoring Engine (Unit 1.B & 2.A)
Processes high-volume offline transaction batches with vectorized execution and summary analytics.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

try:
    from ml.models.registry import load_model, get_feature_names
except ImportError:
    from ml.models.registry import load_model, get_feature_names


def score_batch(
    input_df: pd.DataFrame,
    output_path: Path | str | None = None,
    chunk_size: int = 1000,
) -> dict[str, Any]:
    """
    Score a large batch of transaction records.
    Vectorized execution across chunks, outputting scored dataframe with risk levels.
    """
    start_time = time.perf_counter()
    model = load_model()
    feature_names = get_feature_names()

    missing_cols = set(feature_names) - set(input_df.columns)
    if missing_cols:
        raise ValueError(f"Batch dataset missing features: {sorted(missing_cols)}")

    scored_records = []
    total_rows = len(input_df)

    if total_rows == 0:
        raise ValueError("Batch dataset must contain at least one transaction.")
    if chunk_size < 1:
        raise ValueError("chunk_size must be a positive integer.")

    for i in range(0, total_rows, chunk_size):
        chunk = input_df.iloc[i:i + chunk_size].copy()
        X = chunk[feature_names]
        probabilities = model.predict_proba(X)[:, 1]

        chunk["fraud_probability"] = probabilities
        chunk["risk_level"] = [
            "high" if p >= 0.5 else ("medium" if p >= 0.2 else "low")
            for p in probabilities
        ]
        scored_records.append(chunk)

    result_df = pd.concat(scored_records, ignore_index=True)

    if output_path:
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix == ".parquet":
            result_df.to_parquet(out, index=False)
        else:
            result_df.to_csv(out, index=False)

    duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
    high_risk_count = int((result_df["risk_level"] == "high").sum())
    med_risk_count = int((result_df["risk_level"] == "medium").sum())
    low_risk_count = int((result_df["risk_level"] == "low").sum())

    return {
        "status": "COMPLETED",
        "total_records_scored": total_rows,
        "duration_ms": duration_ms,
        "throughput_records_per_sec": round(total_rows / (duration_ms / 1000.0), 1) if duration_ms > 0 else 0.0,
        "risk_breakdown": {
            "high": high_risk_count,
            "medium": med_risk_count,
            "low": low_risk_count,
        },
        "output_path": str(output_path) if output_path else None,
    }


if __name__ == "__main__":
    sample_path = ROOT / "data" / "creditcard_sample.csv"
    if sample_path.exists():
        df_sample = pd.read_csv(sample_path)
        res = score_batch(df_sample, output_path=ROOT / "data" / "batch_scored_results.csv")
        print("Batch scoring test complete:", res)
