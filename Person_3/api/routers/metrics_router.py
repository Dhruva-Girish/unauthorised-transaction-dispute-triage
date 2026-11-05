"""
metrics_router.py — Prometheus Metrics Exposition Endpoint (Unit 2.C)
"""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi import APIRouter, Response

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from observability.metrics_collector import get_latest_prometheus_metrics

router = APIRouter(tags=["Metrics"])


@router.get("/metrics")
def prometheus_metrics():
    """Exposes application and model metrics in Prometheus text exposition format."""
    data = get_latest_prometheus_metrics()
    return Response(content=data, media_type="text/plain; version=0.0.4; charset=utf-8")
