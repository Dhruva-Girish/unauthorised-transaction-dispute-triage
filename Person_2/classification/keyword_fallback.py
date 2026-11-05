"""
keyword_fallback.py — Deterministic Keyword Fallback Classifier (Unit 2.D & Person 2)
Guarantees resilient classification when LLM APIs are unreachable or error out.
"""

from __future__ import annotations

from typing import Any
from .classifier_interface import ComplaintClassifier, VALID_CATEGORIES


class KeywordFallbackClassifier(ComplaintClassifier):
    """Deterministic keyword-based complaint classification."""

    def classify(self, complaint_text: str, transaction_id: str) -> dict[str, Any]:
        category = self.classify_text(complaint_text)
        return {
            "category": category,
            "provider": "keyword_classifier",
            "confidence": 0.85 if category != "unknown" else 0.40,
            "fallback_used": True,
        }

    @staticmethod
    def classify_text(text: str) -> str:
        text = text.lower()

        if any(w in text for w in [
            "didn't make", "did not make", "unauthorized", "unauthorised",
            "without my permission", "not mine", "fraud", "didn't authorize",
            "did not authorize", "didn't authorise", "did not authorise",
            "stolen card", "card compromised", "scam charge", "stolen",
            "unknown charge", "unknown debit", "unknown payment", "not recognized",
            "charged my card", "someone charged", "asleep",
        ]):
            return "unauthorized_transaction"

        if any(w in text for w in [
            "charged twice", "duplicate", "double charged",
            "twice for the same", "billed twice", "second charge",
            "charged 2 times", "billed two times",
        ]):
            return "duplicate_payment"

        if any(w in text for w in [
            "not delivered", "never delivered", "never arrived",
            "did not receive", "not received", "haven't received",
            "have not received", "not arrived", "package missing",
        ]):
            return "goods_not_received"

        if any(w in text for w in [
            "wrong amount", "billing", "incorrect charge",
            "cancelled but charged", "canceled but charged",
            "recurring charge", "subscription cancelled",
            "subscription", "billed again", "recurring",
        ]):
            return "billing_dispute"

        return "unknown"
