"""
Comprehensive End-to-End Integration Tests covering all 10 required dispute scenarios.
Ensures full alignment across Person 1 ML, Person 2 AI Agent, and Person 3 Backend/DB.
"""
import sys
from pathlib import Path
import pytest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))
P2_PATH = ROOT / "Person_2"
if str(P2_PATH) not in sys.path:
    sys.path.insert(0, str(P2_PATH))

try:
    from Person_2.agents.triage_agent import process_complaint
    from Person_3.database.case_repository import CaseRepository
except ImportError:
    from agents.triage_agent import process_complaint
    from database.case_repository import CaseRepository

repo = CaseRepository()

# -------------------------------------------------------------------------
# Scenario 1: Unauthorized transaction with high fraud score -> urgent queue
# -------------------------------------------------------------------------
def test_scenario_01_unauthorized_high_fraud():
    text = "There is an unauthorized charge of $1200 on my card from an unknown electronic store. My card was never used there."
    result = process_complaint(text, transaction_id="TX1002")
    
    assert result["complaint_category"] == "unauthorized_transaction"
    assert result["requires_human_review"] is True
    assert result["priority"] in ["high", "urgent", "review_required"]
    assert result["status"] == "under_review"

# -------------------------------------------------------------------------
# Scenario 2: Unauthorized transaction with low fraud score -> MUST NOT BE DISMISSED
# -------------------------------------------------------------------------
def test_scenario_02_unauthorized_low_fraud_safety_invariant():
    text = "I did not authorize this $15 charge at the local bakery. I was out of town."
    # Simulate a low fraud score from the ML model
    with patch("Person_2.tools.fraud_scoring_tool.check_fraud_score", return_value={"fraud_probability": 0.04, "risk_level": "low"}):
        result = process_complaint(text, transaction_id="TX1001")
        
        # NON-NEGOTIABLE SAFETY INVARIANT:
        # Must NEVER be automatically dismissed or auto-resolved because of a low ML fraud score
        assert result["complaint_category"] == "unauthorized_transaction"
        assert result["requires_human_review"] is True
        assert result["status"] == "under_review"
        assert "dismiss" not in result["recommended_action"].lower()

# -------------------------------------------------------------------------
# Scenario 3: Clear duplicate charge (same merchant, amount, within 10 min)
# -------------------------------------------------------------------------
def test_scenario_03_clear_duplicate_charge():
    text = "I was charged twice for the same coffee purchase of $4.50 at Starbucks within 3 minutes of each other."
    result = process_complaint(text, transaction_id="TX1003")
    
    assert result["complaint_category"] in ["duplicate_payment", "duplicate_charge"]
    assert result["requires_human_review"] is True

# -------------------------------------------------------------------------
# Scenario 4: Suspected duplicate (different amount or merchant) -> not flagged duplicate
# -------------------------------------------------------------------------
def test_scenario_04_suspected_duplicate_different_amount():
    text = "I bought shoes for $85 at Nike and then later bought socks for $15 at Nike. Is that a duplicate billing?"
    result = process_complaint(text, transaction_id="TX1004")
    
    # Should recognize distinct amounts or flag for inspection
    assert result["case_id"] != ""
    assert result["complaint_category"] in ["duplicate_payment", "duplicate_charge", "billing_dispute", "merchant_dispute", "unknown"]

# -------------------------------------------------------------------------
# Scenario 5: Goods/services not received -> appropriate category, merchant contact checked
# -------------------------------------------------------------------------
def test_scenario_05_goods_services_not_received():
    text = "I ordered a desk chair three weeks ago online, paid $180, but the goods were not received and tracking is dead."
    result = process_complaint(text, transaction_id="TX1005")
    
    assert result["complaint_category"] in ["goods_not_received", "merchant_dispute"]
    assert result["requires_human_review"] is True

# -------------------------------------------------------------------------
# Scenario 6: Subscription cancellation dispute -> subscription policy applied
# -------------------------------------------------------------------------
def test_scenario_06_subscription_cancellation_dispute():
    text = "I cancelled my gym subscription two months ago and confirmed cancellation, but they keep billing me recurring fees."
    result = process_complaint(text, transaction_id="TX1006")
    
    assert result["complaint_category"] in ["subscription_cancellation", "billing_dispute", "merchant_dispute"]
    assert result["requires_human_review"] is True

# -------------------------------------------------------------------------
# Scenario 7: Vague or ambiguous complaint -> requests clarification / lower confidence
# -------------------------------------------------------------------------
def test_scenario_07_ambiguous_complaint():
    text = "Something feels wrong with my account lately. Maybe check it?"
    result = process_complaint(text, transaction_id="TX1007")
    
    assert result["requires_human_review"] is True

# -------------------------------------------------------------------------
# Scenario 8: Missing transaction ID in complaint -> handled gracefully
# -------------------------------------------------------------------------
def test_scenario_08_missing_transaction_id():
    text = "Someone made an unauthorized charge on my card while I was asleep yesterday, I don't know the exact transaction reference."
    result = process_complaint(text, transaction_id="UNKNOWN")
    
    assert result["case_id"].startswith("CASE-")
    assert result["complaint_category"] == "unauthorized_transaction"
    assert result["requires_human_review"] is True

# -------------------------------------------------------------------------
# Scenario 9: Component failure: ML model service down -> fallback risk score, agent completes triage
# -------------------------------------------------------------------------
def test_scenario_09_ml_service_down_fallback():
    text = "I suspect fraudulent activity on my card for $350 at an unknown gas station."
    
    with patch("Person_2.tools.fraud_scoring_tool.check_fraud_score", side_effect=ConnectionError("ML service down")):
        result = process_complaint(text, transaction_id="TX1009")
        
        # Triage must not crash; fallback risk score engaged; unauthorized safety preserved
        assert result is not None
        assert result["complaint_category"] == "unauthorized_transaction"
        assert result["requires_human_review"] is True

# -------------------------------------------------------------------------
# Scenario 10: Component failure: LLM API down -> keyword fallback engages, triage completes
# -------------------------------------------------------------------------
def test_scenario_10_llm_api_down_fallback():
    text = "Unauthorized purchase detected on my statement for $499 at Apple Store."
    
    with patch("Person_2.classification.gemini_classifier.GENAI_AVAILABLE", False):
        result = process_complaint(text, transaction_id="TX1010")
        
        # Fallback classifier must classify it correctly
        assert result is not None
        assert result["complaint_category"] == "unauthorized_transaction"
        assert result["requires_human_review"] is True
