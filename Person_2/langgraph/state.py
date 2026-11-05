"""
state.py — LangGraph Workflow State Contract (Unit 4.A)
Defines the typed graph state dictionary passed across LangGraph nodes.
"""

from __future__ import annotations

from typing import Any, TypedDict, List, Optional


class DisputeState(TypedDict, total=False):
    """Execution state for LangGraph dispute triage workflow."""
    case_id: str
    complaint_text: str
    transaction_id: str
    customer_id: Optional[str]

    # Classification stage
    complaint_category: str
    classification_confidence: float
    classifier_provider: str

    # Tool outputs
    transaction: Optional[dict[str, Any]]
    transaction_found: bool
    customer_history: list[dict[str, Any]]
    duplicate_matches: list[dict[str, Any]]

    # ML Scoring
    fraud_probability: Optional[float]
    risk_level: str

    # RAG Retrieval
    retrieved_policies: list[str]

    # Guardrails & Decision
    evidence_summary: list[str]
    recommended_action: str
    priority: str
    requires_human_review: bool
    status: str
    error: Optional[str]

    # Telemetry
    execution_steps: list[str]
    total_latency_ms: float
