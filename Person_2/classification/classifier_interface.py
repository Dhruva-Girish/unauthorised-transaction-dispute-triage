"""
classifier_interface.py — Complaint Classifier Interface (Unit 3.A, 3.G)
Defines the standard complaint classification contract and category domain.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

VALID_CATEGORIES = {
    "unauthorized_transaction",
    "duplicate_payment",
    "goods_not_received",
    "billing_dispute",
    "other",
    "unknown",
}


class ComplaintClassifier(ABC):
    """Abstract interface for complaint classification providers."""

    @abstractmethod
    def classify(self, complaint_text: str, transaction_id: str) -> dict[str, Any]:
        """
        Classify a natural language customer complaint.
        Returns dict: {'category': str, 'provider': str, 'confidence': float, ...}
        """
        pass
