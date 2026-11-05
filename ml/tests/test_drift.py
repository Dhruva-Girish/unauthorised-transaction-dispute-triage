"""
test_drift.py — Tests for Kolmogorov-Smirnov and PSI Ingestion Drift Monitoring (Unit 1.D)
"""

import sys
from pathlib import Path
import numpy as np
import pandas as pd
from ml.monitoring.drift_monitor import DataDriftMonitor, calculate_psi


def test_psi_identical_distributions():
    data = np.random.normal(0, 1, 500)
    psi = calculate_psi(data, data)
    assert psi < 0.05


def test_psi_shifted_distribution_detected():
    base = np.random.normal(0, 1, 500)
    shifted = np.random.normal(5, 1, 500)
    psi = calculate_psi(base, shifted)
    assert psi > 0.25


def test_drift_monitor_clean_batch():
    base_df = pd.DataFrame({
        "Amount": np.random.exponential(50.0, 500),
        "V14": np.random.normal(0, 1, 500),
        "V17": np.random.normal(0, 1, 500),
        "V12": np.random.normal(0, 1, 500),
        "V4": np.random.normal(0, 1, 500),
    })
    monitor = DataDriftMonitor(baseline_df=base_df)

    # Identical current batch should report no drift
    clean_batch = base_df.sample(200, random_state=42)
    report = monitor.check_drift(clean_batch)
    assert report["has_drift"] is False
    assert len(report["drifted_features"]) == 0


def test_drift_monitor_drifted_batch():
    base_df = pd.DataFrame({
        "Amount": np.random.exponential(50.0, 500),
        "V14": np.random.normal(0, 1, 500),
        "V17": np.random.normal(0, 1, 500),
        "V12": np.random.normal(0, 1, 500),
        "V4": np.random.normal(0, 1, 500),
    })
    monitor = DataDriftMonitor(baseline_df=base_df)

    # Corrupted / drifted batch
    drifted_batch = pd.DataFrame({
        "Amount": np.random.exponential(500.0, 200),
        "V14": np.random.normal(-8.0, 1, 200),
        "V17": np.random.normal(-6.0, 1, 200),
        "V12": np.random.normal(-5.0, 1, 200),
        "V4": np.random.normal(5.0, 1, 200),
    })

    report = monitor.check_drift(drifted_batch)
    assert report["has_drift"] is True
    assert len(report["drifted_features"]) > 0
    assert "retraining" in report["recommendation"].lower()
