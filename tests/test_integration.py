"""
test_integration.py — Integration and System Tests for Member 3.

Verifies the integration among:
  - Member 1's ML fraud detection model
  - Member 2's AI agent decision workflow
  - Member 3's Case Store, Agent Ops logging, and evaluation pipeline

Run with:
    pytest tests/test_integration.py -v
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from agent.agent import process_complaint
from agent.case_store import load_cases
from app.agent_ops import (
    load_raw_logs,
    get_case_traces,
    compute_agent_ops_metrics,
    AgentTrace,
)
from ml.fraud_model import predict_fraud, FEATURE_NAMES


class TestSharedDataFiles:
    """Validate data files and ML artifacts."""

    def test_transactions_file_exists(self):
        tx_file = ROOT / "data" / "transactions.json"
        assert tx_file.exists(), "data/transactions.json must exist"
        data = json.loads(tx_file.read_text(encoding="utf-8"))
        assert isinstance(data, list) and len(data) >= 3
        for item in data:
            assert "transaction_id" in item
            assert "amount" in item
            assert "customer_id" in item

    def test_test_cases_file_exists(self):
        tc_file = ROOT / "data" / "test_cases.json"
        assert tc_file.exists(), "data/test_cases.json must exist"
        cases = json.loads(tc_file.read_text(encoding="utf-8"))
        assert isinstance(cases, list) and len(cases) >= 5

    def test_ml_model_artifacts_exist(self):
        model_path = ROOT / "ml" / "artifacts" / "fraud_pipeline.joblib"
        metrics_path = ROOT / "ml" / "model_metrics.json"
        assert model_path.exists(), "fraud_pipeline.joblib must exist"
        assert metrics_path.exists(), "model_metrics.json must exist"


class TestMLModelIntegration:
    """Verify Member 1's fraud prediction function."""

    def test_predict_fraud_valid_features(self):
        features = {name: 0.0 for name in FEATURE_NAMES}
        result = predict_fraud(features)
        assert "fraud_probability" in result
        assert "risk_level" in result
        assert 0.0 <= result["fraud_probability"] <= 1.0
        assert result["risk_level"] in {"low", "medium", "high"}


class TestAgentIntegration:
    """Verify Member 2's agent pipeline interface and triage behavior."""

    EXPECTED_KEYS = {
        "case_id",
        "transaction_id",
        "complaint_category",
        "fraud_probability",
        "risk_level",
        "priority",
        "evidence_summary",
        "recommended_action",
        "requires_human_review",
        "status",
        "error",
    }

    def test_process_complaint_schema(self):
        result = process_complaint(
            "I did not make this transaction.",
            "TX1001",
        )
        assert self.EXPECTED_KEYS.issubset(result.keys())
        assert result["complaint_category"] == "unauthorized_transaction"
        assert result["requires_human_review"] is True
        assert result["status"] == "under_review"

    def test_missing_transaction_handling(self):
        result = process_complaint(
            "I did not make this payment.",
            "TX-NOT-FOUND",
        )
        assert result["error"] == "Transaction not found."
        assert result["fraud_probability"] is None
        assert result["requires_human_review"] is True

    def test_duplicate_payment_workflow(self):
        result = process_complaint(
            "I was charged twice for the same purchase.",
            "TX1002",
        )
        assert result["complaint_category"] == "duplicate_payment"
        assert result["requires_human_review"] is True
        # TX1002 has a duplicate TX1003 in data/transactions.json
        evidence_text = " ".join(result["evidence_summary"])
        assert "possible matching" in evidence_text or "Transaction record retrieved" in evidence_text

    def test_safety_rule_no_auto_resolve_on_low_score(self):
        """A customer fraud claim must never be auto-resolved or dismissed."""
        result = process_complaint(
            "I did not authorize this charge.",
            "TX1001",
        )
        assert result["requires_human_review"] is True
        assert result["status"] != "resolved"


class TestAgentOpsAndPersistence:
    """Verify Case Store and Agent Ops event logging."""

    def test_case_is_persisted(self):
        result = process_complaint(
            "My order was never delivered.",
            "TX1002",
        )
        cases = load_cases()
        saved_ids = {c["case_id"] for c in cases}
        assert result["case_id"] in saved_ids

    def test_agent_ops_logs_recorded(self):
        result = process_complaint(
            "Billing dispute regarding subscription charge.",
            "TX1002",
        )
        traces = get_case_traces()
        assert result["case_id"] in traces
        event_types = [e["event_type"] for e in traces[result["case_id"]]]
        assert "case_received" in event_types
        assert "triage_completed" in event_types

    def test_agent_ops_metrics(self):
        metrics = compute_agent_ops_metrics()
        assert metrics["total_cases"] >= 1
        assert metrics["total_events"] >= 1
        assert 0.0 <= metrics["success_rate"] <= 100.0
        assert "category_distribution" in metrics
        assert "priority_distribution" in metrics

    def test_agent_trace_context_manager(self):
        with AgentTrace("Complaint text", "TX1001") as trace:
            res = process_complaint("I did not authorize this transaction.", "TX1001")
            trace.set_result(res)

        assert trace.duration_ms >= 0.0
        assert trace.result is not None
