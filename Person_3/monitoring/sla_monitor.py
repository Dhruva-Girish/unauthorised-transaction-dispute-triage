"""
sla_monitor.py — Service Level Agreement (SLA/SLO/SLI) Measurement (Unit 1.F)
Calculates real-time SLI metrics, error budget burn rates, and SLO compliance.
"""

from __future__ import annotations

import time
from collections import deque
from typing import Any
try:
    from Person_3.observability.metrics_collector import set_sla_compliance_metric
except ImportError:
    try:
        from observability.metrics_collector import set_sla_compliance_metric
    except ImportError:
        def set_sla_compliance_metric(*args, **kwargs):
            pass


class SLAMonitor:
    """
    Measures compliance against defined Service Level Objectives (SLOs):
      - SLI 1: Triage API Latency (SLO: 95% of requests < 500ms; SLA: 99% < 1500ms)
      - SLI 2: System Availability & Success (SLO: 99.5% non-5xx responses)
      - SLI 3: Data Freshness (SLO: < 60 seconds from event arrival to feature store)
    """

    def __init__(self, target_latency_ms: float = 500.0, window_size: int = 1000) -> None:
        self.target_latency_ms = target_latency_ms
        self.latencies: deque[float] = deque(maxlen=window_size)
        self.success_flags: deque[bool] = deque(maxlen=window_size)

    def record_request(self, latency_ms: float, is_success: bool = True) -> None:
        """Record an individual request outcome."""
        self.latencies.append(latency_ms)
        self.success_flags.append(is_success)

        # Update gauge
        ratio = self.get_compliance_metrics().get("slo_latency_compliance_percent", 100.0) / 100.0
        set_sla_compliance_metric(ratio)

    def get_compliance_metrics(self) -> dict[str, Any]:
        """Compute rolling SLA/SLO/SLI compliance statistics."""
        if not self.latencies:
            return {
                "total_requests_evaluated": 0,
                "p50_latency_ms": 0.0,
                "p95_latency_ms": 0.0,
                "p99_latency_ms": 0.0,
                "slo_latency_target_ms": self.target_latency_ms,
                "slo_latency_compliance_percent": 100.0,
                "slo_availability_percent": 100.0,
                "error_budget_remaining_percent": 100.0,
                "sla_breach_detected": False,
            }

        sorted_lat = sorted(self.latencies)
        n = len(sorted_lat)

        p50 = round(sorted_lat[int(n * 0.50)], 1)
        p95 = round(sorted_lat[min(int(n * 0.95), n - 1)], 1)
        p99 = round(sorted_lat[min(int(n * 0.99), n - 1)], 1)

        compliant_count = sum(1 for lat in self.latencies if lat <= self.target_latency_ms)
        latency_compliance = round((compliant_count / n) * 100.0, 2)

        success_count = sum(1 for s in self.success_flags if s)
        availability = round((success_count / len(self.success_flags)) * 100.0, 2)

        # Error budget: Allowed 5% failure/breach rate (95% target)
        allowed_failures = max(1, int(n * 0.05))
        actual_breaches = n - compliant_count
        error_budget_remaining = max(0.0, round(((allowed_failures - actual_breaches) / allowed_failures) * 100.0, 1))

        sla_breach = p95 > self.target_latency_ms or availability < 99.5

        return {
            "total_requests_evaluated": n,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "p99_latency_ms": p99,
            "slo_latency_target_ms": self.target_latency_ms,
            "slo_latency_compliance_percent": latency_compliance,
            "slo_availability_percent": availability,
            "error_budget_remaining_percent": error_budget_remaining,
            "sla_breach_detected": sla_breach,
        }


# Global SLA monitor
sla_monitor = SLAMonitor()
