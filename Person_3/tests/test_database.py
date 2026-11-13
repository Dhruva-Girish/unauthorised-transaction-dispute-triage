"""
Unit tests for CaseRepository and SQLite database operations in Person 3.
"""
import sys
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))

try:
    from Person_3.database.case_repository import CaseRepository
    from Person_3.database.connection import get_db_connection
except ImportError:
    from database.case_repository import CaseRepository
    from database.connection import get_db_connection

def test_database_connection():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode;")
    mode = cursor.fetchone()[0]
    conn.close()
    assert mode.lower() == "wal"

def test_save_and_retrieve_case():
    repo = CaseRepository()
    test_id = "TEST_CASE_001"
    
    case_data = {
        "case_id": test_id,
        "transaction_id": "TX9999",
        "customer_id": "CUST9999",
        "complaint_text": "Test unauthorized charge of $100",
        "complaint_category": "unauthorized_transaction",
        "priority": "high",
        "risk_level": "high",
        "fraud_probability": 0.88,
        "recommended_action": "escalate_to_human",
        "requires_human_review": True,
        "confidence_score": 0.92,
        "evidence_summary": ["Suspicious charge flagged by unit test."],
        "status": "under_review"
    }
    repo.save_case(case_data)

    # Retrieve case
    retrieved = repo.get_case(test_id)
    assert retrieved is not None
    assert retrieved["case_id"] == test_id
    assert retrieved["transaction_id"] == "TX9999"
    assert retrieved["complaint_category"] == "unauthorized_transaction"
    assert retrieved["requires_human_review"] is True

def test_update_case_status():
    repo = CaseRepository()
    test_id = "TEST_CASE_002"
    case_data = {
        "case_id": test_id,
        "transaction_id": "TX9998",
        "customer_id": "CUST9998",
        "complaint_category": "duplicate_charge",
        "priority": "medium",
        "risk_level": "low",
        "fraud_probability": 0.15,
        "recommended_action": "review_duplicate",
        "requires_human_review": True,
        "status": "under_review"
    }
    repo.save_case(case_data)

    case_data["status"] = "resolved"
    case_data["recommended_action"] = "Refund processed"
    repo.save_case(case_data)

    case = repo.get_case(test_id)
    assert case["status"] == "resolved"
    assert "Refund processed" in case["recommended_action"]

def test_list_cases_filtering():
    repo = CaseRepository()
    cases = repo.list_cases(limit=10)
    assert isinstance(cases, list)
    assert len(cases) >= 1
