"""
enums.py — Common Domain Enumerations
"""

from enum import Enum


class ComplaintCategory(str, Enum):
    UNAUTHORIZED_TRANSACTION = "unauthorized_transaction"
    DUPLICATE_PAYMENT = "duplicate_payment"
    GOODS_NOT_RECEIVED = "goods_not_received"
    BILLING_DISPUTE = "billing_dispute"
    OTHER = "other"
    UNKNOWN = "unknown"

    @classmethod
    def values(cls) -> list[str]:
        return [item.value for item in cls]


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    UNAVAILABLE = "unavailable"


class PriorityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    REVIEW_REQUIRED = "review_required"


class CaseStatus(str, Enum):
    NEW = "new"
    UNDER_REVIEW = "under_review"
    ESCALATED = "escalated"
    RESOLVED = "resolved"


class EventType(str, Enum):
    CASE_RECEIVED = "case_received"
    CLASSIFICATION_COMPLETED = "classification_completed"
    CLASSIFICATION_FALLBACK = "classification_fallback"
    TRANSACTION_RETRIEVED = "transaction_retrieved"
    CUSTOMER_HISTORY_RETRIEVED = "customer_history_retrieved"
    DUPLICATE_CHECK_COMPLETED = "duplicate_check_completed"
    FRAUD_SCORE_COMPUTED = "fraud_score_computed"
    RAG_POLICY_RETRIEVED = "rag_policy_retrieved"
    TRIAGE_COMPLETED = "triage_completed"
    CASE_SAVED = "case_saved"
    PROCESSING_ERROR = "processing_error"
    CASE_STORAGE_ERROR = "case_storage_error"
    CASE_ESCALATED = "case_escalated"
    FRAUD_ALERT = "fraud_alert"
