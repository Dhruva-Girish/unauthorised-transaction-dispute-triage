"""
triage_router.py — REST API Endpoints for Dispute Triage (Unit 1.C, 4.B)
Exposes synchronous real-time triage and asynchronous message queue ingestion.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from database.case_repository import case_repo
from message_queue.queue_broker import message_broker
from monitoring.sla_monitor import sla_monitor
from observability.metrics_collector import record_triage_latency
from telemetry.otel_tracer import trace_span
from security.rate_limiter import rate_limit_dependency

router = APIRouter(prefix="/api/v1", tags=["Dispute Triage"])


class DisputeSubmissionPayload(BaseModel):
    complaint_text: str = Field(..., min_length=5, description="Natural language dispute complaint")
    transaction_id: str = Field(..., min_length=1, description="Card transaction identifier")
    customer_id: str | None = None
    channel: str = Field(default="web")


@router.post("/triage", dependencies=[Depends(rate_limit_dependency)])
def submit_dispute_triage(payload: DisputeSubmissionPayload):
    """
    Synchronous Real-Time Dispute Triage:
    Executes Person 2's LangGraph agent, runs fraud scoring against Person 1,
    applies RAG policies and safety guardrails, saves case in DB, and returns recommendation.
    """
    t0 = time.perf_counter()

    with trace_span("triage_endpoint", {"transaction_id": payload.transaction_id}):
        try:
            from Person_2.agents.triage_agent import process_complaint
            result = process_complaint(payload.complaint_text, payload.transaction_id)
            case_repo.save_case(result)

            duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            sla_monitor.record_request(duration_ms, is_success=True)
            record_triage_latency(
                category=result.get("complaint_category", "unknown"),
                priority=result.get("priority", "review_required"),
                duration_sec=duration_ms / 1000.0,
            )

            result["api_duration_ms"] = duration_ms
            return result
        except Exception as exc:
            duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            sla_monitor.record_request(duration_ms, is_success=False)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Dispute triage execution error: {exc}",
            )


@router.post("/async-triage", dependencies=[Depends(rate_limit_dependency)])
def submit_async_dispute(payload: DisputeSubmissionPayload):
    """
    Asynchronous Message Queue Ingestion:
    Enqueues the complaint into the background message queue for decoupled worker processing.
    """
    msg_id = message_broker.publish(
        topic="disputes.inbound",
        payload={
            "complaint_text": payload.complaint_text,
            "transaction_id": payload.transaction_id,
            "customer_id": payload.customer_id,
            "channel": payload.channel,
        },
    )

    return {
        "status": "QUEUED",
        "message_id": msg_id,
        "transaction_id": payload.transaction_id,
        "notice": "Complaint enqueued for asynchronous background triage.",
        "queue_depth": message_broker.size(),
    }
