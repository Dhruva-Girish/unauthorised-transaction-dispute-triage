"""
test_langgraph.py — Tests for LangGraph Stateful Workflow (Unit 4.A)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from langgraph.dispute_graph import run_langgraph_workflow


def test_langgraph_unauthorized_flow():
    res = run_langgraph_workflow("I did not authorize this payment.", "TX1001")
    assert res["complaint_category"] == "unauthorized_transaction"
    assert res["requires_human_review"] is True
    assert res["status"] == "under_review"
    assert "classify_complaint" in res["execution_steps"]
    assert "lookup_transaction" in res["execution_steps"]
    assert "synthesize_decision" in res["execution_steps"]


def test_langgraph_missing_transaction_flow():
    res = run_langgraph_workflow("Unauthorized debit on my card.", "TX-MISSING-999")
    assert res["transaction_found"] is False
    assert res["error"] == "Transaction not found."
    assert res["requires_human_review"] is True


def test_langgraph_duplicate_payment_flow():
    res = run_langgraph_workflow("Charged twice for the exact same order.", "TX1002")
    assert res["complaint_category"] == "duplicate_payment"
    assert "check_duplicates" in res["execution_steps"]
    assert res["requires_human_review"] is True
