"""
shared_contracts — Authoritative Schemas, Enums, and Contracts
Shared across Person 1 (ML), Person 2 (Agent), and Person 3 (Backend & Dashboard).
"""

from .enums import (
    ComplaintCategory,
    RiskLevel,
    PriorityLevel,
    CaseStatus,
    EventType,
)
from .schemas import (
    TransactionRecord,
    ModelFeatures,
    FraudPredictionRequest,
    FraudPredictionResponse,
    ComplaintRequest,
    TriageResult,
    WebhookPayload,
    IngestionValidationResult,
    DriftReport,
)
from .config import SystemSettings, get_settings

__all__ = [
    "ComplaintCategory",
    "RiskLevel",
    "PriorityLevel",
    "CaseStatus",
    "EventType",
    "TransactionRecord",
    "ModelFeatures",
    "FraudPredictionRequest",
    "FraudPredictionResponse",
    "ComplaintRequest",
    "TriageResult",
    "WebhookPayload",
    "IngestionValidationResult",
    "DriftReport",
    "SystemSettings",
    "get_settings",
]
