"""
drift_monitor.py — Data Drift Monitoring at Ingestion (Unit 1.D)
Calculates Kolmogorov-Smirnov (KS) statistic and Population Stability Index (PSI)
comparing incoming transaction distributions against reference baseline data.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any
import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).resolve().parent.parent
BASELINE_PATH = ROOT / "data" / "reference_baseline.csv"


def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
    """
    Calculate Population Stability Index (PSI) between two 1D distributions.
    Rule of thumb:
      PSI < 0.1: No significant change
      0.1 <= PSI < 0.25: Moderate shift
      PSI >= 0.25: Significant drift detected
    """
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    # Determine quantile bins from baseline
    quantiles = np.linspace(0, 100, num_buckets + 1)
    bins = np.percentile(baseline, quantiles)
    bins[0] -= 1e-5
    bins[-1] += 1e-5
    bins = np.unique(bins)

    if len(bins) < 2:
        return 0.0

    b_counts, _ = np.histogram(baseline, bins=bins)
    c_counts, _ = np.histogram(current, bins=bins)

    b_pct = (b_counts + 1e-4) / (len(baseline) + 1e-4 * len(b_counts))
    c_pct = (c_counts + 1e-4) / (len(current) + 1e-4 * len(c_counts))

    psi_val = np.sum((c_pct - b_pct) * np.log(c_pct / b_pct))
    return float(psi_val)


class DataDriftMonitor:
    """Monitors ingestion feature drift using KS-test and PSI."""

    def __init__(self, baseline_df: pd.DataFrame | None = None) -> None:
        if baseline_df is not None:
            self.baseline_df = baseline_df
        elif BASELINE_PATH.exists():
            self.baseline_df = pd.read_csv(BASELINE_PATH)
        else:
            self.baseline_df = pd.DataFrame()

    def check_drift(
        self,
        current_df: pd.DataFrame,
        features: list[str] | None = None,
        ks_alpha: float = 0.05,
        psi_threshold: float = 0.25,
    ) -> dict[str, Any]:
        """
        Evaluate drift on specified numeric features.
        Returns drift report with p-values, KS statistics, and PSI metrics.
        """
        if self.baseline_df.empty:
            return {
                "has_drift": False,
                "error": "No baseline dataset available for comparison.",
                "drifted_features": [],
            }

        features = features or ["Amount", "V14", "V17", "V12", "V4"]
        drift_results = {}
        drifted_features = []

        for feature in features:
            if feature not in current_df.columns or feature not in self.baseline_df.columns:
                continue

            base_vals = self.baseline_df[feature].dropna().to_numpy()
            curr_vals = current_df[feature].dropna().to_numpy()

            if len(base_vals) == 0 or len(curr_vals) == 0:
                continue

            # Two-sample Kolmogorov-Smirnov test
            ks_res = stats.ks_2samp(base_vals, curr_vals)
            ks_stat = float(ks_res.statistic)
            p_val = float(ks_res.pvalue)

            # PSI calculation
            psi_score = calculate_psi(base_vals, curr_vals)

            is_drift = (p_val < ks_alpha) or (psi_score >= psi_threshold)
            if is_drift:
                drifted_features.append(feature)

            drift_results[feature] = {
                "ks_statistic": round(ks_stat, 4),
                "p_value": round(p_val, 4),
                "psi_score": round(psi_score, 4),
                "is_drifted": is_drift,
            }

        has_drift = len(drifted_features) > 0
        recommendation = (
            "Trigger automated model retraining and verify upstream data ingestion pipeline."
            if has_drift
            else "Distributions are stable. Feature contracts maintained."
        )

        return {
            "has_drift": has_drift,
            "drifted_features": drifted_features,
            "monitored_feature_count": len(features),
            "feature_metrics": drift_results,
            "recommendation": recommendation,
        }
