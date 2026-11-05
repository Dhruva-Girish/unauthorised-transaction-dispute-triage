"""
test_prompts.py — Tests for Prompt Management and Version Comparison (Unit 3.B)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from prompts.registry import prompt_registry


def test_registered_prompts():
    versions = prompt_registry.list_versions()
    assert "v1.0.0_baseline" in versions
    assert "v2.0.0_structured_cot" in versions


def test_prompt_retrieval():
    prompt = prompt_registry.get_prompt("v2.0.0_structured_cot")
    assert "Strict Rules of Engagement" in prompt
    assert "Triage Reasoning Structure" in prompt


def test_prompt_comparison():
    comp = prompt_registry.compare_prompts("v1.0.0_baseline", "v2.0.0_structured_cot")
    assert "version_a" in comp
    assert "version_b" in comp
    assert comp["diff_line_count"] > 0
