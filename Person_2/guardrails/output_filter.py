"""
output_filter.py — LLM Output Filtering and Safety Validation (Unit 3.F)
Scans generated recommendations to prevent hallucinations, toxicity, or unauthorized
promises (e.g. guaranteeing autonomous refunds or dismissing fraud without review).
"""

from __future__ import annotations

import re
from typing import Any

FORBIDDEN_OUTPUT_PHRASES = [
    r"i\s+have\s+refunded",
    r"refund\s+(has\s+been\s+)?issued",
    r"we\s+have\s+credited\s+your\s+account",
    r"your\s+card\s+has\s+been\s+(blocked|canceled)",
    r"claim\s+is\s+(denied|dismissed|rejected)\s+because\s+the\s+model",
    r"model\s+says\s+it\s+is\s+not\s+fraud",
]


class OutputFilterGuardrail:
    """Validates LLM-generated recommendations against compliance boundaries."""

    def __init__(self) -> None:
        self.forbidden_patterns = [re.compile(p, re.IGNORECASE) for p in FORBIDDEN_OUTPUT_PHRASES]

    def validate(self, text: str) -> dict[str, Any]:
        """
        Check if agent output violates role boundaries.
        Returns: {'is_valid': bool, 'violations': list[str]}
        """
        violations = []
        for pattern in self.forbidden_patterns:
            if pattern.search(text):
                violations.append(pattern.pattern)

        return {
            "is_valid": len(violations) == 0,
            "violations": violations,
            "safety_action": "REJECT_OUTPUT" if violations else "ACCEPT_OUTPUT",
        }
