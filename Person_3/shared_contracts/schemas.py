"""
schemas.py — Standard Pydantic Models and Data Contracts
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from pydantic import BaseModel, Field

from .enums import ComplaintCategory, RiskLevel, PriorityLevel, CaseStatus


class ModelFeatures(BaseModel):
    """30-feature vector expected by the Credit Card Fraud model."""
    Time: float = Field(default=0.0, description="Seconds elapsed since first transaction")
    V1: float = 0.0
    V2: float = 0.0
    V3: float = 0.0
    V4: float = 0.0
    V5: float = 0.0
    V6: float = 0.0
    V7: float = 0.0
    V8: float = 0.0
    V9: float = 0.0
    V10: float = 0.0
    V11: float = 0.0
    V12: float = 0.0
    V13: float = 0.0
    V14: float = 0.0
    V15: float = 0.0
    V16: float = 0.0
    V17: float = 0.0
    V18: float = 0.0
    V19: float = 0.0
    V20: float = 0.0
    V21: float = 0.0
    V22: float = 0.0
    V23: float = 0.0
    V24: float = 0.0
    V25: float = 0.0
    V26: float = 0.0
    V27: float = 0.0
    V28: float = 0.0
    Amount: float = Field(default=0.0, ge=0.0, description="Transaction amount")

    model_config = {"extra": "forbid"}


class TransactionRecord(BaseModel):
    """Authoritative ledger transaction record."""
    transaction_id: str = Field(..., min_length=1)
    customer_id: str = Field(..., min_length=1)
    amount: float = Field(..., gt=0.0)
    currency: str = Field(default="INR", min_length=3, max_length=3)
    merchant: str = Field(..., min_length=1)
    timestamp: str
    country: str = Field(default="IN", min_length=2, max_length=2)
    device_id: str | None = None
    model_features: dict[str, float] | None = None


class FraudPredictionRequest(BaseModel):
    """Request payload for Person 1 ML Model Service."""
    transaction_id: str | None = None
    features: dict[str, float]


class FraudPredictionResponse(BaseModel):
    """Response payload returned by Person 1 ML Model Service."""
    fraud_probability: float = Field(..., ge=0.0, le=1.0)
    risk_level: RiskLevel
    model_name: str = "random_forest_fraud_pipeline"
    inference_latency_ms: float = 0.0
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ComplaintRequest(BaseModel):
    """Inbound customer complaint submission."""
    complaint_text: str = Field(..., min_length=5, description="Natural language dispute text")
    transaction_id: str = Field(..., min_length=1, description="Target transaction ID")
    customer_id: str | None = None
    channel: str = Field(default="web", description="Submission channel (web, mobile, api)")


class TriageResult(BaseModel):
    """Complete, evidence-based dispute triage recommendation."""
    case_id: str
    transaction_id: str
    complaint_category: str
    fraud_probability: float | None = None
    risk_level: str = "unavailable"
    priority: str = "review_required"
    evidence_summary: list[str] = Field(default_factory=list)
    recommended_action: str
    requires_human_review: bool = True
    status: str = "under_review"
    error: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class WebhookPayload(BaseModel):
    """Outgoing webhook event payload."""
    event_id: str
    event_type: str
    timestamp: str
    data: dict[str, Any]
    signature: str | None = None


class IngestionValidationResult(BaseModel):
    """Data contract validation result."""
    is_valid: bool
    record_count: int
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    schema_version: str = "1.0.0"


class DriftReport(BaseModel):
    """Statistical data drift analysis output."""
    metric_name: str = "Kolmogorov-Smirnov & PSI"
    has_drift: bool
    drifted_features: list[str] = Field(default_factory=list)
    ks_statistics: dict[str, float] = Field(default_factory=dict)
    p_values: dict[str, float] = Field(default_factory=dict)
    psi_scores: dict[str, float] = Field(default_factory=dict)
    recommendation: str
