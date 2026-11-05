"""
grpc_client.py — gRPC Client Demo and Integration Tester (Unit 1.C)
Demonstrates binary remote procedure calls against DisputeTriageService.
"""

from __future__ import annotations

import time
import grpc
from .dispute_service_pb2 import FraudPredictionRequest, TriageDisputeRequest
from .dispute_service_pb2_grpc import DisputeTriageServiceStub


class DisputeGrpcClient:
    """Client wrapper for DisputeTriageService gRPC server."""

    def __init__(self, host: str = "localhost", port: int = 50051) -> None:
        self.target = f"{host}:{port}"
        self.channel = grpc.insecure_channel(self.target)
        self.stub = DisputeTriageServiceStub(self.channel)

    def predict_fraud(self, features: dict[str, float], transaction_id: str = "TX1001"):
        """Call PredictFraud RPC."""
        req = FraudPredictionRequest(transaction_id=transaction_id, features=features)
        return self.stub.PredictFraud(req)

    def triage_dispute(self, complaint_text: str, transaction_id: str, customer_id: str = "CUST001"):
        """Call TriageDispute RPC."""
        req = TriageDisputeRequest(
            complaint_text=complaint_text,
            transaction_id=transaction_id,
            customer_id=customer_id,
        )
        return self.stub.TriageDispute(req)

    def close(self) -> None:
        self.channel.close()
