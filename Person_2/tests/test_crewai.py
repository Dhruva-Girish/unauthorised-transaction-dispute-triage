"""
test_crewai.py — Tests for CrewAI Multi-Agent Coordination (Unit 4.A)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from crewai.fraud_crew import fraud_crew


def test_crewai_investigation_workflow():
    report = fraud_crew.run_investigation("I did not authorize this charge.", "TX1001")
    assert report["orchestration_type"] == "CrewAI_Multi_Agent"
    assert len(report["agents_involved"]) == 3
    assert report["complaint_category"] == "unauthorized_transaction"
    assert report["requires_human_review"] is True
    assert len(report["evidence_summary"]) >= 3
    assert len(report["policy_citations"]) >= 1
