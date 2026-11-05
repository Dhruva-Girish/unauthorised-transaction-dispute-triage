"""
injection_defense.py — Prompt Injection & Adversarial Attack Defense (Unit 3.F)
Scans inbound customer complaint text for adversarial prompt injection, jailbreaks,
and system instruction override attempts before passing to LLM agents.
"""

from __future__ import annotations

import re
from typing import Any

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(the\s+)?(above|rules|system)",
    r"you\s+are\s+now\s+(in\s+)?(developer\s+mode|dan|unrestricted)",
    r"print\s+(your\s+)?(system\s+prompt|instructions)",
    r"output\s+(the\s+)?system\s+prompt",
    r"bypass\s+(all\s+)?filters",
    r"approve\s+(this\s+)?refund\s+immediately",
    r"execute\s+script",
    r"<script.*?>",
    r"javascript:",
]


class InjectionDefenseGuardrail:
    """Detects and neutralizes prompt injection attempts in natural language inputs."""

    def __init__(self) -> None:
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def inspect(self, text: str) -> dict[str, Any]:
        """
        Scan text for prompt injection.
        Returns: {'is_safe': bool, 'flagged_patterns': list[str], 'sanitized_text': str}
        """
        flagged = []
        for pattern in self.compiled_patterns:
            matches = pattern.findall(text)
            if matches:
                flagged.append(pattern.pattern)

        is_safe = len(flagged) == 0

        # Sanitize by stripping suspected adversarial instructions
        sanitized = text
        if not is_safe:
            for pattern in self.compiled_patterns:
                sanitized = pattern.sub("[REDACTED_ADVERSARIAL_INSTRUCTION]", sanitized)

        return {
            "is_safe": is_safe,
            "flagged_patterns": flagged,
            "sanitized_text": sanitized.strip(),
            "risk": "HIGH" if not is_safe else "LOW",
        }
