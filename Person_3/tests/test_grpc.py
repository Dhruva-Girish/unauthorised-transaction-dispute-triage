"""
Unit tests for gRPC service and client in Person 3.
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
    from Person_3.grpc.grpc_server import DisputeGrpcServicer
    from Person_3.grpc.dispute_service_pb2 import TriageDisputeRequest, FraudPredictionRequest
except ImportError:
    from grpc.grpc_server import DisputeGrpcServicer
    from grpc.dispute_service_pb2 import TriageDisputeRequest, FraudPredictionRequest

def test_grpc_servicer_triage():
    servicer = DisputeGrpcServicer()
    request = TriageDisputeRequest(
        complaint_text="I did not make this transaction of $300 at Best Buy",
        transaction_id="TX1001"
    )

    response = servicer.TriageDispute(request, context=None)
    assert response is not None
    assert response.case_id != ""
    assert response.complaint_category == "unauthorized_transaction"
    assert response.requires_human_review is True
    assert response.priority in ["high", "medium", "urgent", "review_required"]

def test_grpc_servicer_predict_fraud():
    servicer = DisputeGrpcServicer()
    features = {
        "amount": 450.0,
        "is_foreign": 1.0,
        "time_diff_hours": 0.5,
        "distance_km": 150.0,
        "is_card_present": 0.0,
    }
    request = FraudPredictionRequest(features=features)
    response = servicer.PredictFraud(request, context=None)
    assert response is not None
    assert response.fraud_probability >= 0.0
    assert response.risk_level in ["low", "medium", "high", "unavailable"]
