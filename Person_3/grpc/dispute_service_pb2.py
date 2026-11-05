"""
dispute_service_pb2.py — Generated / Python Stubs for DisputeTriageService (Unit 1.C)
Provides Python message types for FraudPrediction and TriageDispute RPCs.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass
class FraudPredictionRequest:
    transaction_id: str = ""
    features: dict[str, float] = field(default_factory=dict)


@dataclass
class FraudPredictionResponse:
    fraud_probability: float = 0.0
    risk_level: str = "unavailable"
    model_name: str = "fraud_pipeline"
    inference_latency_ms: float = 0.0


@dataclass
class TriageDisputeRequest:
    complaint_text: str = ""
    transaction_id: str = ""
    customer_id: str = ""


@dataclass
class TriageDisputeResponse:
    case_id: str = ""
    transaction_id: str = ""
    complaint_category: str = "unknown"
    fraud_probability: float = 0.0
    risk_level: str = "unavailable"
    priority: str = "review_required"
    evidence_summary: list[str] = field(default_factory=list)
    recommended_action: str = ""
    requires_human_review: bool = True
    status: str = "under_review"
    error: str = ""
    execution_latency_ms: float = 0.0
