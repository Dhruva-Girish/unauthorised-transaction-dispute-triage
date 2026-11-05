"""
triage_agent.py — Authoritative AI Agent Execution Interface (Person 2 Integration Contract)
Coordinates complaint understanding, LangGraph workflow execution, tool calling,
RAG retrieval, safety guardrails, and evidence-grounded recommendation generation.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from langgraph.dispute_graph import run_langgraph_workflow
from guardrails.safety_checker import SafetyChecker
from guardrails.output_filter import OutputFilterGuardrail
from observability.trace_logger import agent_logger
from observability.token_tracker import token_tracker

_output_filter = OutputFilterGuardrail()


def process_complaint(complaint_text: str, transaction_id: str) -> dict[str, Any]:
    """
    Authoritative Person 2 agent execution interface.
    Consumed by Person 3 FastAPI backend, CLI, and Streamlit dashboard.

    Input:
      - complaint_text: Natural language customer complaint.
      - transaction_id: Target transaction ID.

    Returns:
      Triage result dictionary containing:
        - case_id
        - transaction_id
        - complaint_category
        - fraud_probability
        - risk_level
        - priority
        - evidence_summary
        - recommended_action
        - requires_human_review (ALWAYS True for unauthorized transactions)
        - status
        - error
    """
    t0 = time.perf_counter()
    case_id = f"CASE-{uuid4().hex[:8].upper()}"

    agent_logger.log_event(case_id, "case_received", {"transaction_id": transaction_id})

    try:
        # Run stateful LangGraph workflow
        graph_output = run_langgraph_workflow(complaint_text, transaction_id)

        actual_case_id = graph_output.get("case_id", case_id)
        category = graph_output.get("complaint_category", "unknown")
        prob = graph_output.get("fraud_probability")
        risk = graph_output.get("risk_level", "unavailable")
        action = graph_output.get("recommended_action", "Review dispute manually.")
        priority = graph_output.get("priority", "review_required")
        evidence = graph_output.get("evidence_summary", [])
        status = graph_output.get("status", "under_review")
        error = graph_output.get("error")

        # Output Filter Guardrail check
        output_check = _output_filter.validate(action)
        if not output_check["is_valid"]:
            action = "Escalate for manual supervisor review due to compliance policy constraints."
            priority = "high"

        # Safety Check Invariant: Non-dismissal guarantee for unauthorized complaints
        hr_enforced, status_enforced, safety_notes = SafetyChecker.enforce_unauthorized_transaction_safety(
            complaint_category=category,
            fraud_probability=prob,
            risk_level=risk,
            current_status=status,
            requires_human_review=True,
        )

        total_lat = round((time.perf_counter() - t0) * 1000.0, 2)

        # Record token tracking
        token_tracker.record_call(
            model_name=graph_output.get("classifier_provider", "gemini-2.5-flash"),
            prompt_text=complaint_text,
            completion_text=action,
            latency_ms=total_lat,
        )

        # Log completion event
        agent_logger.log_event(
            actual_case_id,
            "triage_completed",
            {
                "category": category,
                "priority": priority,
                "status": status_enforced,
                "risk_level": risk,
                "requires_human_review": hr_enforced,
            },
            duration_ms=total_lat,
        )

        return {
            "case_id": actual_case_id,
            "transaction_id": transaction_id,
            "complaint_category": category,
            "fraud_probability": prob,
            "risk_level": risk,
            "priority": priority,
            "evidence_summary": evidence,
            "recommended_action": action,
            "requires_human_review": hr_enforced,
            "status": status_enforced,
            "error": error,
            "execution_metadata": {
                "steps": graph_output.get("execution_steps", []),
                "latency_ms": total_lat,
                "safety_notes": safety_notes,
            },
        }

    except Exception as exc:
        # Safe fallback: Never auto-dismiss or drop dispute on unhandled error
        agent_logger.log_event(case_id, "processing_error", {"error_type": type(exc).__name__, "message": str(exc)})
        return {
            "case_id": case_id,
            "transaction_id": transaction_id,
            "complaint_category": "unknown",
            "fraud_probability": None,
            "risk_level": "unavailable",
            "priority": "review_required",
            "evidence_summary": [],
            "recommended_action": "Review the processing error and investigate the complaint.",
            "requires_human_review": True,
            "status": "under_review",
            "error": f"Processing encountered an unexpected error: {exc}. Manual review required.",
        }
