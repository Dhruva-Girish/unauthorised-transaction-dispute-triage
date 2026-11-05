"""
health_router.py — System Health, Liveness, Readiness & SLA Inspection Endpoints (Unit 1.F & 2.D)
"""

from __future__ import annotations

import sys
from pathlib import Path
from fastapi import APIRouter

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.case_repository import case_repo
from monitoring.sla_monitor import sla_monitor
from message_queue.queue_broker import message_broker
from reliability.circuit_breaker import gemini_breaker, ml_model_breaker

router = APIRouter(prefix="/api/v1", tags=["Health & SLA"])


@router.get("/health")
def system_health():
    """Liveness and readiness health check examining core subsystems."""
    db_ok = True
    try:
        case_repo.list_cases(limit=1)
    except Exception:
        db_ok = False

    return {
        "status": "HEALTHY" if db_ok else "DEGRADED",
        "service": "dispute-triage-backend",
        "subsystems": {
            "database": "CONNECTED" if db_ok else "ERROR",
            "message_queue": f"ACTIVE ({message_broker.size()} pending)",
            "gemini_circuit_breaker": gemini_breaker.status(),
            "ml_model_circuit_breaker": ml_model_breaker.status(),
        },
    }


@router.get("/sla")
def sla_compliance():
    """Return live Service Level Agreement (SLA/SLO/SLI) performance metrics."""
    return sla_monitor.get_compliance_metrics()
