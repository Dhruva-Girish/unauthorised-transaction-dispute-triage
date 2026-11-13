"""
metrics_collector.py — Prometheus Observability Metrics (Unit 2.C)
Exposes metrics for API latency, request throughput, SLA compliance, and error budgets.
"""

from __future__ import annotations

import time

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
    HTTP_REQUEST_COUNT = _get_or_create(
        Counter,
        "dispute_api_requests_total",
        "Total HTTP requests to the Dispute Triage API",
        ["method", "endpoint", "status_code"],
    )

    TRIAGE_LATENCY_HISTOGRAM = _get_or_create(
        Histogram,
        "dispute_triage_duration_seconds",
        "Latency distribution of end-to-end complaint triage",
        ["category", "priority"],
        buckets=[0.05, 0.1, 0.25, 0.5, 0.75, 1.0, 2.0, 5.0],
    )

    ACTIVE_CASES_GAUGE = _get_or_create(
        Gauge,
        "dispute_active_cases_total",
        "Total active dispute cases currently in the review queue",
        ["status"],
    )

    SLA_COMPLIANCE_RATIO = _get_or_create(
        Gauge,
        "dispute_sla_compliance_ratio",
        "Ratio of requests processed within the target SLA threshold (<500ms)",
    )

    DATA_DRIFT_GAUGE = _get_or_create(
        Gauge,
        "ml_data_drift_detected",
        "Binary indicator of whether data drift is currently detected (0=normal, 1=drift)",
    )

    # Initialize non-empty baseline series for Prometheus & Grafana discovery
    try:
        SLA_COMPLIANCE_RATIO.set(1.0)
        DATA_DRIFT_GAUGE.set(0)
        ACTIVE_CASES_GAUGE.labels(status="under_review").set(0)
        HTTP_REQUEST_COUNT.labels(method="GET", endpoint="/api/v1/health", status_code="200")
        HTTP_REQUEST_COUNT.labels(method="POST", endpoint="/api/v1/triage", status_code="200")
        TRIAGE_LATENCY_HISTOGRAM.labels(category="unauthorized_transaction", priority="high").observe(0.05)
    except Exception:
        pass


def record_request_metric(method: str, endpoint: str, status_code: int) -> None:
    if PROMETHEUS_AVAILABLE:
        HTTP_REQUEST_COUNT.labels(method=method, endpoint=endpoint, status_code=str(status_code)).inc()


def record_triage_latency(category: str, priority: str, duration_sec: float) -> None:
    if PROMETHEUS_AVAILABLE:
        TRIAGE_LATENCY_HISTOGRAM.labels(category=category, priority=priority).observe(duration_sec)


def set_active_cases_metric(status: str, count: int) -> None:
    if PROMETHEUS_AVAILABLE:
        ACTIVE_CASES_GAUGE.labels(status=status).set(count)


def set_sla_compliance_metric(ratio: float) -> None:
    if PROMETHEUS_AVAILABLE:
        SLA_COMPLIANCE_RATIO.set(ratio)


def get_latest_prometheus_metrics() -> bytes:
    if PROMETHEUS_AVAILABLE:
        return generate_latest()
    return b"# Prometheus client library not available\n"
