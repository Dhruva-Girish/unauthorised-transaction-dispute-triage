"""
Unit and integration tests for Person 3 FastAPI backend endpoints.
"""
import sys
from pathlib import Path
import pytest
from starlette.testclient import TestClient

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))

try:
    from Person_3.backend.main import app
except ImportError:
    from backend.main import app

client = TestClient(app)

def test_api_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"].lower() == "healthy"
    assert "subsystems" in data or "database" in data

def test_api_sla_endpoint():
    response = client.get("/api/v1/sla")
    assert response.status_code == 200
    data = response.json()
    assert "p50_latency_ms" in data or "compliance_ratio" in data or "slo_target_latency_ms" in data

def test_api_metrics_endpoint():
    response = client.get("/metrics")
    assert response.status_code == 200
    assert "dispute" in response.text.lower() or "http" in response.text.lower()

def test_api_cases_list():
    response = client.get("/api/v1/cases?limit=5")
    assert response.status_code == 200
    data = response.json()
    assert "cases" in data
    assert isinstance(data["cases"], list)

def test_api_sync_triage():
    payload = {
        "complaint_text": "I noticed an unauthorized payment of $120 on my statement",
        "customer_id": "CUST_API_TEST",
        "transaction_id": "TX1001"
    }
    response = client.post("/api/v1/triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "case_id" in data
    assert data["complaint_category"] == "unauthorized_transaction"
    # CRITICAL INVARIANT: Unauthorized disputes must require human review
    assert data["requires_human_review"] is True

def test_api_async_triage():
    payload = {
        "complaint_text": "Duplicate charge on my card for $45",
        "customer_id": "CUST_ASYNC_TEST",
        "transaction_id": "TX1003"
    }
    response = client.post("/api/v1/async-triage", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "QUEUED"
    assert "message_id" in data
