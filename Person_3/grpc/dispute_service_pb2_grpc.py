"""
dispute_service_pb2_grpc.py — gRPC Servicer and Stub Interfaces (Unit 1.C)
"""

from __future__ import annotations

import grpc
from .dispute_service_pb2 import (
    FraudPredictionRequest,
    FraudPredictionResponse,
    TriageDisputeRequest,
    TriageDisputeResponse,
)


class DisputeTriageServiceServicer:
    """Base servicer class for DisputeTriageService RPC handler."""

    def PredictFraud(self, request: FraudPredictionRequest, context) -> FraudPredictionResponse:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")

    def TriageDispute(self, request: TriageDisputeRequest, context) -> TriageDisputeResponse:
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details("Method not implemented!")
        raise NotImplementedError("Method not implemented!")


class DisputeTriageServiceStub:
    """Client stub for invoking DisputeTriageService RPC methods."""

    def __init__(self, channel: grpc.Channel) -> None:
        self.channel = channel
        self.PredictFraud = channel.unary_unary(
            "/dispute.v1.DisputeTriageService/PredictFraud",
            request_serializer=lambda req: str(req.__dict__).encode("utf-8"),
            response_deserializer=lambda b: FraudPredictionResponse(**eval(b.decode("utf-8"))),
        )
        self.TriageDispute = channel.unary_unary(
            "/dispute.v1.DisputeTriageService/TriageDispute",
            request_serializer=lambda req: str(req.__dict__).encode("utf-8"),
            response_deserializer=lambda b: TriageDisputeResponse(**eval(b.decode("utf-8"))),
        )


def add_DisputeTriageServiceServicer_to_server(servicer: DisputeTriageServiceServicer, server: grpc.Server) -> None:
    """Registers RPC handlers with the gRPC server."""
    rpc_method_handlers = {
        "PredictFraud": grpc.unary_unary_rpc_method_handler(
            servicer.PredictFraud,
            request_deserializer=lambda b: FraudPredictionRequest(**eval(b.decode("utf-8"))),
            response_serializer=lambda resp: str(resp.__dict__).encode("utf-8"),
        ),
        "TriageDispute": grpc.unary_unary_rpc_method_handler(
            servicer.TriageDispute,
            request_deserializer=lambda b: TriageDisputeRequest(**eval(b.decode("utf-8"))),
            response_serializer=lambda resp: str(resp.__dict__).encode("utf-8"),
        ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
        "dispute.v1.DisputeTriageService", rpc_method_handlers
    )
    server.add_generic_rpc_handlers((generic_handler,))
