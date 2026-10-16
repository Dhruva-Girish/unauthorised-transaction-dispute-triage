
import agent.agent as agent_module

from agent.agent import (
    process_complaint,
    classify_complaint_basic,
)


def test_unauthorized_classification():
    assert classify_complaint_basic(
        "I did not make this transaction."
    ) == "unauthorized_transaction"


def test_duplicate_classification():
    assert classify_complaint_basic(
        "I was charged twice for the same purchase."
    ) == "duplicate_payment"


def test_goods_not_received_classification():
    assert classify_complaint_basic(
        "My order was paid for but never delivered."
    ) == "goods_not_received"


def test_missing_transaction(monkeypatch):
    # Mock Gemini so this test does not call the real API.
    monkeypatch.setattr(
        agent_module,
        "classify_complaint_with_gemini",
        lambda complaint_text, transaction_id: (
            "unauthorized_transaction"
        ),
    )

    result = process_complaint(
        "I did not make this payment.",
        "TX-NOT-FOUND",
    )

    assert result["fraud_probability"] is None
    assert result["requires_human_review"] is True
    assert result["error"] == "Transaction not found."


def test_duplicate_case(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "classify_complaint_with_gemini",
        lambda complaint_text, transaction_id: "duplicate_payment",
    )

    result = process_complaint(
        "I was charged twice for the same purchase.",
        "TX1002",
    )

    assert result["complaint_category"] == "duplicate_payment"
    assert result["transaction_id"] == "TX1002"
    assert result["error"] is None
    assert result["requires_human_review"] is True


def test_gemini_classification_success(monkeypatch):
    monkeypatch.setattr(
        agent_module,
        "classify_complaint_with_gemini",
        lambda complaint_text, transaction_id: (
            "goods_not_received"
        ),
    )

    result = process_complaint(
        "My order was never delivered.",
        "TX1002",
    )

    assert result["complaint_category"] == "goods_not_received"
    assert result["status"] == "under_review"
    assert result["requires_human_review"] is True


def test_gemini_failure_uses_keyword_fallback(monkeypatch):
    def simulate_gemini_failure(complaint_text, transaction_id):
        raise RuntimeError("Simulated API failure")

    monkeypatch.setattr(
        agent_module,
        "classify_complaint_with_gemini",
        simulate_gemini_failure,
    )

    result = process_complaint(
        "I did not authorize this transaction.",
        "TX1001",
    )

    assert result["complaint_category"] == "unauthorized_transaction"
    assert result["status"] == "under_review"
    assert result["requires_human_review"] is True
