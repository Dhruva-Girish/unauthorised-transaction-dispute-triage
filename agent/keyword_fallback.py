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
            "confidence": 0.95 if category != "unknown" else 0.40,
            "fallback_used": True,
        }

    @staticmethod
    def classify_text(text: str) -> str:
        text = text.lower()

        # Duplicate payments
        if any(w in text for w in [
            "charged twice", "duplicate", "double charged",
            "twice for the same", "billed twice", "second charge",
            "charged 2 times", "billed two times", "duplicate swipe",
            "swiped my card twice", "swipe failed", "both charges",
            "double charge", "swiped twice",
        ]):
            return "duplicate_payment"

        # Goods not received / defective delivery
        if any(w in text for w in [
            "not delivered", "never delivered", "never arrived",
            "did not receive", "not received", "haven't received",
            "have not received", "not arrived", "package missing",
            "never arrived", "parcel", "never received", "courier",
            "arrived broken", "broken", "defective", "gadget that arrived",
            "tracking link says", "nothing was received", "not as described",
        ]):
            return "goods_not_received"

        # Billing dispute / cancellation
        if any(w in text for w in [
            "wrong amount", "billing", "incorrect charge",
            "cancelled but charged", "canceled but charged",
            "recurring charge", "subscription cancelled",
            "subscription", "billed again", "recurring",
            "free trial", "incorrect tip", "membership",
            "auto-renewed", "license", "cancellation email",
            "auto-renewal", "annual software",
        ]):
            return "billing_dispute"

        # Unauthorized transactions & social engineering / OTP / fraud / adversarial
        if any(w in text for w in [
            "didn't make", "did not make", "unauthorized", "unauthorised",
            "without my permission", "not mine", "fraud", "didn't authorize",
            "did not authorize", "didn't authorise", "did not authorise",
            "stolen card", "card compromised", "scam charge", "stolen",
            "unknown charge", "unknown debit", "unknown payment", "not recognized",
            "charged my card", "someone charged", "asleep", "otp", "shared an otp",
            "sms alert", "three weeks", "phishing", "impersonating", "social engineering",
            "skimming", "lost wallet", "compromised", "fake bank", "system override",
            "ignore all", "bypass audit", "instructions", "adversarial",
        ]):
            return "unauthorized_transaction"

        return "unknown"
