"""
metrics_collector.py — Prometheus Metrics for ML Model Serving (Unit 2.C)
Exposes counters, histograms, and gauges for prediction latency, throughput,
fraud probability distribution, and data drift alerts.
"""

from __future__ import annotations

import time
from typing import Any

try:
    from prometheus_client import REGISTRY, Counter, Histogram, Gauge, generate_latest
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False


def _get_or_create(metric_cls, name, doc, *args, **kwargs):
    if not PROMETHEUS_AVAILABLE:
        return None
    if name in REGISTRY._names_to_collectors:
        return REGISTRY._names_to_collectors[name]
    return metric_cls(name, doc, *args, **kwargs)


if PROMETHEUS_AVAILABLE:
    MODEL_PREDICTION_COUNT = _get_or_create(
        Counter,
        "ml_model_predictions_total",
        "Total number of predictions served by the ML fraud model",
        ["model_name", "risk_level"],
    )

    MODEL_INFERENCE_LATENCY = _get_or_create(
        Histogram,
        "ml_model_inference_latency_seconds",
        "Inference latency distribution of the ML fraud model",
        ["model_name"],
        buckets=[0.001, 0.005, 0.010, 0.025, 0.050, 0.100, 0.250, 0.500, 1.0],
    )

    FRAUD_PROBABILITY_GAUGE = _get_or_create(
        Gauge,
        "ml_model_latest_fraud_probability",
        "Most recent fraud probability score output by the model",
        ["model_name"],
    )

    DATA_DRIFT_ALERT_GAUGE = _get_or_create(
        Gauge,
        "ml_data_drift_detected",
        "Flag indicating whether data drift was detected at ingestion (1=drift, 0=clean)",
    )


def record_prediction_metric(model_name: str, probability: float, risk_level: str, latency_sec: float) -> None:
    """Record a completed prediction event in Prometheus metrics."""
    if PROMETHEUS_AVAILABLE:
        MODEL_PREDICTION_COUNT.labels(model_name=model_name, risk_level=risk_level).inc()
        MODEL_INFERENCE_LATENCY.labels(model_name=model_name).observe(latency_sec)
        FRAUD_PROBABILITY_GAUGE.labels(model_name=model_name).set(probability)


def record_drift_metric(has_drift: bool) -> None:
    """Set Prometheus drift indicator gauge."""
    if PROMETHEUS_AVAILABLE:
        DATA_DRIFT_ALERT_GAUGE.set(1 if has_drift else 0)


def get_prometheus_metrics_bytes() -> bytes:
    """Generate Prometheus exposition text for the /metrics HTTP endpoint."""
    if PROMETHEUS_AVAILABLE:
        return generate_latest()
    return b"# Prometheus client library not available\n"
