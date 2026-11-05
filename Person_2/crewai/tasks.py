"""
tasks.py — Multi-Agent Investigation Tasks (Unit 4.A)
"""

from __future__ import annotations

from typing import Any

try:
    from crewai import Task
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


def create_fact_gathering_task(investigator_agent: Any, complaint_text: str, transaction_id: str) -> Any:
    desc = (
        f"Analyze customer complaint: '{complaint_text}' for transaction ID: '{transaction_id}'. "
        "Retrieve ledger transaction record, customer history, and evaluate duplicate charge indicators."
    )
    expected_output = "Detailed factual summary of the transaction, duplicate status, and customer narrative."
    if CREWAI_AVAILABLE and not isinstance(investigator_agent, dict):
        return Task(description=desc, expected_output=expected_output, agent=investigator_agent)
    return {"description": desc, "expected_output": expected_output}


def create_compliance_review_task(compliance_agent: Any, category: str) -> Any:
    desc = (
        f"Review complaint category '{category}' against card dispute policies and Regulation E. "
        "Confirm that human review is strictly mandated if category is unauthorized_transaction."
    )
    expected_output = "Regulatory determination with applicable policy clauses and required customer safeguards."
    if CREWAI_AVAILABLE and not isinstance(compliance_agent, dict):
        return Task(description=desc, expected_output=expected_output, agent=compliance_agent)
    return {"description": desc, "expected_output": expected_output}


def create_final_triage_task(risk_auditor_agent: Any, fraud_risk: str) -> Any:
    desc = (
        f"Correlate ML fraud risk '{fraud_risk}' with investigator findings and compliance constraints. "
        "Assign priority queue (high, medium, review_required) and recommend definitive next actions."
    )
    expected_output = "Final triage recommendation with assigned queue, priority level, and evidence summary."
    if CREWAI_AVAILABLE and not isinstance(risk_auditor_agent, dict):
        return Task(description=desc, expected_output=expected_output, agent=risk_auditor_agent)
    return {"description": desc, "expected_output": expected_output}
