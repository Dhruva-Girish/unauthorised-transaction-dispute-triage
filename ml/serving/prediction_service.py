"""FastAPI and enriched prediction interface for the fraud model."""

from __future__ import annotations

import time
from typing import Any

import pandas as pd
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel

from ml.models.registry import get_feature_names, get_model_metadata, load_model
from ml.monitoring.metrics_collector import (
    get_prometheus_metrics_bytes,
    record_prediction_metric,
)
from ml.preprocessing.data_validator import validate_feature_vector
from ml.serving.caching import PredictionCache

_cache = PredictionCache(maxsize=10000, ttl_seconds=300.0)


def predict_fraud(
    transaction_features: dict[str, Any], use_cache: bool = True
) -> dict[str, Any]:
    """Score one transaction and return the service-level response metadata."""
    start_time = time.perf_counter()
    if use_cache:
        cached = _cache.get(transaction_features)
        if cached is not None:
            result = cached.copy()
            result["cached"] = True
            result["inference_latency_ms"] = round(
                (time.perf_counter() - start_time) * 1000.0, 3
            )
            return result

    valid, errors = validate_feature_vector(transaction_features)
    if not valid:
        raise ValueError(f"Feature validation failed: {'; '.join(errors)}")

    names = get_feature_names()
    row = pd.DataFrame(
        [{name: float(transaction_features[name]) for name in names}],
        columns=names,
    )
    probability = float(load_model().predict_proba(row)[0, 1])
    risk_level = "high" if probability >= 0.5 else (
        "medium" if probability >= 0.2 else "low"
    )
    latency_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
    model_name = get_model_metadata().get("model_name", "fraud_pipeline")
    result = {
        "fraud_probability": probability,
        "risk_level": risk_level,
        "model_name": model_name,
        "inference_latency_ms": latency_ms,
        "cached": False,
    }
    record_prediction_metric(model_name, probability, risk_level, latency_ms / 1000.0)
    if use_cache:
        _cache.put(transaction_features, result)
    return result


app = FastAPI(
    title="Card Fraud Detection Model Service",
    description="Member 1 fraud scoring API.",
    version="1.0.0",
)


class PredictionPayload(BaseModel):
    transaction_id: str | None = None
    features: dict[str, float]


@app.get("/health")
def health_check() -> dict[str, Any]:
    return {
        "status": "HEALTHY",
        "service": "ml-fraud-model",
        "model_metadata": get_model_metadata(),
    }


@app.get("/model-info")
def model_info() -> dict[str, Any]:
    return get_model_metadata()


@app.get("/cache/stats")
def cache_stats() -> dict[str, Any]:
    return _cache.stats()


@app.get("/metrics", response_class=Response)
def metrics() -> Response:
    return Response(
        content=get_prometheus_metrics_bytes(),
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )


@app.post("/predict")
def predict_endpoint(payload: PredictionPayload) -> dict[str, Any]:
    try:
        result = predict_fraud(payload.features)
        if payload.transaction_id:
            result["transaction_id"] = payload.transaction_id
        return result
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Inference error: {exc}") from exc


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
