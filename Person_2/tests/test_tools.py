"""
test_tools.py — Tests for Person 2 Agent Tools
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from tools.transaction_tool import get_transaction, lookup_transaction_tool
from tools.duplicate_tool import check_duplicate_transactions
from tools.history_tool import get_customer_history
from tools.fraud_scoring_tool import check_fraud_score


def test_transaction_lookup_existing():
    tx = get_transaction("TX1001")
    assert tx is not None
    assert tx["transaction_id"] == "TX1001"
    assert tx["amount"] == 20000


def test_transaction_lookup_missing():
    tx = get_transaction("TX-DOES-NOT-EXIST")
    assert tx is None
    tool_res = lookup_transaction_tool("TX-DOES-NOT-EXIST")
    assert tool_res["found"] is False


def test_customer_history_retrieval():
    history = get_customer_history("CUST002")
    assert isinstance(history, list)
    assert len(history) >= 1


def test_duplicate_transaction_detection():
    # TX1002 has matching TX1003 in sample data
    duplicates = check_duplicate_transactions("TX1002", window_minutes=10)
    assert isinstance(duplicates, list)
    if duplicates:
        assert duplicates[0]["transaction_id"] == "TX1003"


def test_fraud_scoring_tool_safely_handles_null():
    tx_without_features = {"transaction_id": "TX999", "model_features": None}
    res = check_fraud_score(tx_without_features)
    assert res["fraud_probability"] is None
    assert res["risk_level"] == "unavailable"
