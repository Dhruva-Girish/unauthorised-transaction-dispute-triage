"""
safety_checker.py — Policy Safety & Evidence-Grounding Enforcer (Unit 3.F)
Enforces the non-negotiable safety invariant: Unauthorized transaction claims must
NEVER be dismissed or auto-resolved due to a low ML fraud score.
"""

from __future__ import annotations

from typing import Any


class SafetyChecker:
    """Enforces dispute triage safety policies and evidence grounding."""

    @staticmethod
    def enforce_unauthorized_transaction_safety(
        complaint_category: str,
        fraud_probability: float | None,
        risk_level: str,
        current_status: str,
        requires_human_review: bool,
    ) -> tuple[bool, str, list[str]]:
        """
        Verify that unauthorized transaction disputes cannot be auto-dismissed.
        Returns (is_compliant, enforced_status, safety_notes).
        """
        safety_notes: list[str] = []

        if complaint_category == "unauthorized_transaction":
            # Safety Invariant 1: Must mandate human review
            if not requires_human_review:
                safety_notes.append("Safety Violation: Unauthorized transaction MUST require human review. Enforced True.")
                requires_human_review = True

            # Safety Invariant 2: Cannot be marked resolved autonomously
            if current_status == "resolved":
                safety_notes.append("Safety Violation: Unauthorized transaction cannot be auto-resolved. Overridden to 'under_review'.")
                current_status = "under_review"

            # Safety Invariant 3: Low fraud score must explicitly not dismiss claim
            if risk_level == "low" or (fraud_probability is not None and fraud_probability < 0.2):
                safety_notes.append("Safety Note: Low ML fraud score noted, but claim must remain under review per banking safety rules.")

        return requires_human_review, current_status, safety_notes

    @staticmethod
    def verify_evidence_grounding(
        evidence_summary: list[str],
        transaction_found: bool,
        fraud_score_present: bool,
    ) -> list[str]:
        """
        Detect hallucinations: ensure evidence items do not assert facts not in evidence.
        """
        warnings = []
        evidence_blob = " ".join(evidence_summary).lower()

        if not transaction_found and "retrieved successfully" in evidence_blob:
            warnings.append("Hallucination Warning: Evidence asserts transaction was found when database returned None.")

        if not fraud_score_present and ("fraud model returned risk level" in evidence_blob and "unavailable" not in evidence_blob):
            warnings.append("Hallucination Warning: Evidence asserts fraud score present when model score is None.")

        return warnings
