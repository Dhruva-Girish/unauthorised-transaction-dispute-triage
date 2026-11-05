"""
grpc_server.py — High-Performance gRPC Microservice Server (Unit 1.C)
Exposes low-latency binary RPC endpoints for ML fraud prediction and complaint triage.
"""

from __future__ import annotations

import sys
import time
from concurrent import futures
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import grpc
from .dispute_service_pb2 import (
    FraudPredictionRequest,
    FraudPredictionResponse,
    TriageDisputeRequest,
    TriageDisputeResponse,
)
from .dispute_service_pb2_grpc import (
    DisputeTriageServiceServicer,
    add_DisputeTriageServiceServicer_to_server,
)
from database.case_repository import case_repo


class DisputeGrpcServicer(DisputeTriageServiceServicer):
    """Servicer implementing gRPC remote procedure calls."""

    def PredictFraud(self, request: FraudPredictionRequest, context) -> FraudPredictionResponse:
        """gRPC handler for ML fraud scoring."""
        t0 = time.perf_counter()
        try:
            from Person_1.serving.prediction_service import predict_fraud
            raw_features = dict(request.features) if request.features else {}
            # Ensure complete 30-feature vector for model pipeline
            amount = float(raw_features.get("Amount", raw_features.get("amount", 0.0)))
            time_val = float(raw_features.get("Time", raw_features.get("time", 0.0)))
            norm_features = {
                "Time": time_val,
                "Amount": amount,
                **{f"V{i}": float(raw_features.get(f"V{i}", 0.0)) for i in range(1, 29)},
            }
            pred = predict_fraud(norm_features)
            dur = round((time.perf_counter() - t0) * 1000.0, 2)
            return FraudPredictionResponse(
                fraud_probability=float(pred.get("fraud_probability", 0.0)),
                risk_level=str(pred.get("risk_level", "unavailable")),
                model_name=str(pred.get("model_name", "fraud_pipeline")),
                inference_latency_ms=dur,
            )
        except Exception as exc:
            if context is not None:
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(str(exc))
            return FraudPredictionResponse(
                fraud_probability=0.0,
                risk_level="unavailable",
                model_name="error",
                inference_latency_ms=0.0,
            )

    def TriageDispute(self, request: TriageDisputeRequest, context) -> TriageDisputeResponse:
        """gRPC handler for end-to-end AI agent dispute triage."""
        t0 = time.perf_counter()
        try:
            from Person_2.agents.triage_agent import process_complaint
            result = process_complaint(request.complaint_text, request.transaction_id)
            case_repo.save_case(result)
            dur = round((time.perf_counter() - t0) * 1000.0, 2)

            return TriageDisputeResponse(
                case_id=result.get("case_id", ""),
                transaction_id=result.get("transaction_id", ""),
                complaint_category=result.get("complaint_category", "unknown"),
                fraud_probability=float(result.get("fraud_probability") or 0.0),
                risk_level=result.get("risk_level", "unavailable"),
                priority=result.get("priority", "review_required"),
                evidence_summary=result.get("evidence_summary", []),
                recommended_action=result.get("recommended_action", ""),
                requires_human_review=result.get("requires_human_review", True),
                status=result.get("status", "under_review"),
                error=result.get("error") or "",
                execution_latency_ms=dur,
            )
        except Exception as exc:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(str(exc))
            return TriageDisputeResponse(
                case_id="ERROR",
                transaction_id=request.transaction_id,
                error=str(exc),
            )


def serve(port: int = 50051) -> grpc.Server:
    """Start and return the gRPC server."""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    add_DisputeTriageServiceServicer_to_server(DisputeGrpcServicer(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    return server


if __name__ == "__main__":
    server = serve(50051)
    print("Dispute Triage gRPC Server listening on port 50051...")
    try:
        while True:
            time.sleep(86400)
    except KeyboardInterrupt:
        server.stop(0)
