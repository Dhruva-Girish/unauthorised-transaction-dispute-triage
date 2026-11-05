"""
registry.py — Prompt Versioning and Management Registry (Unit 3.B)
Tracks prompt versions, enables A/B comparisons, and logs prompt change history.
"""

from __future__ import annotations

import difflib
from typing import Any
from .prompt_v1 import SYSTEM_PROMPT_V1
from .prompt_v2 import SYSTEM_PROMPT_V2


class PromptRegistry:
    """Manages prompt templates, version metadata, and comparative analysis."""

    def __init__(self) -> None:
        self._prompts: dict[str, dict[str, Any]] = {
            "v1.0.0_baseline": {
                "version": "1.0.0",
                "tag": "baseline",
                "template": SYSTEM_PROMPT_V1.strip(),
                "author": "Person_2",
                "release_date": "2026-10-15",
                "description": "Initial rule-based instruction prompt with category constraints.",
            },
            "v2.0.0_structured_cot": {
                "version": "2.0.0",
                "tag": "production_default",
                "template": SYSTEM_PROMPT_V2.strip(),
                "author": "Person_2",
                "release_date": "2026-11-01",
                "description": "Chain-of-thought prompt with explicit policy citations and injection defenses.",
            },
        }
        self.default_version = "v2.0.0_structured_cot"

    def get_prompt(self, version: str | None = None) -> str:
        """Retrieve prompt template text for specified version."""
        ver = version or self.default_version
        if ver not in self._prompts:
            raise KeyError(f"Prompt version '{ver}' not found. Available: {list(self._prompts.keys())}")
        return self._prompts[ver]["template"]

    def get_metadata(self, version: str) -> dict[str, Any]:
        """Return version metadata."""
        if version not in self._prompts:
            raise KeyError(f"Prompt version '{ver}' not found.")
        return self._prompts[version]

    def list_versions(self) -> list[str]:
        """List all registered prompt versions."""
        return list(self._prompts.keys())

    def compare_prompts(self, ver_a: str, ver_b: str) -> dict[str, Any]:
        """Compute structural diff and token length delta between two prompt versions."""
        p_a = self.get_prompt(ver_a)
        p_b = self.get_prompt(ver_b)

        diff = list(difflib.unified_diff(
            p_a.splitlines(keepends=True),
            p_b.splitlines(keepends=True),
            fromfile=ver_a,
            tofile=ver_b,
        ))

        return {
            "version_a": ver_a,
            "version_b": ver_b,
            "char_count_a": len(p_a),
            "char_count_b": len(p_b),
            "diff_line_count": len(diff),
            "diff_preview": "".join(diff[:20]),
        }


# Singleton registry
prompt_registry = PromptRegistry()
