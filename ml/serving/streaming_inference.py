"""
streaming_inference.py — Streaming Inference Engine (Unit 1.B & 2.A)
Simulates continuous real-time transaction streaming (Kafka/Pulsar pattern)
with sub-millisecond per-event scoring, windowing, and anomaly dispatch.
"""

from __future__ import annotations

import time
from typing import Iterator, Callable, Any
from .prediction_service import predict_fraud


class StreamingInferenceSimulator:
    """Consumes a continuous stream of transaction events and performs live scoring."""

    def __init__(self, alert_threshold: float = 0.5) -> None:
        self.alert_threshold = alert_threshold
        self.events_processed = 0
        self.alerts_generated = 0
        self.latencies_ms: list[float] = []

    def process_event(self, event: dict[str, Any]) -> dict[str, Any]:
        """Score an incoming streaming event in real time."""
        t0 = time.perf_counter()
        features = event.get("features", event)
        tx_id = event.get("transaction_id", f"STREAM_TX_{self.events_processed}")

        prediction = predict_fraud(features, use_cache=True)
        duration_ms = round((time.perf_counter() - t0) * 1000.0, 3)

        self.events_processed += 1
        self.latencies_ms.append(duration_ms)

        is_alert = prediction["fraud_probability"] >= self.alert_threshold
        if is_alert:
            self.alerts_generated += 1

        return {
            "transaction_id": tx_id,
            "fraud_probability": prediction["fraud_probability"],
            "risk_level": prediction["risk_level"],
            "alert_triggered": is_alert,
            "stream_latency_ms": duration_ms,
        }

    def process_stream(
        self,
        event_stream: Iterator[dict[str, Any]],
        callback: Callable[[dict[str, Any]], None] | None = None,
        max_events: int = 100,
    ) -> dict[str, Any]:
        """Process an iterator stream of events up to max_events."""
        start_time = time.perf_counter()
        count = 0

        for event in event_stream:
            scored = self.process_event(event)
            if callback:
                callback(scored)
            count += 1
            if count >= max_events:
                break

        total_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        avg_lat = round(sum(self.latencies_ms) / len(self.latencies_ms), 3) if self.latencies_ms else 0.0

        return {
            "status": "STREAM_FINISHED",
            "events_processed": self.events_processed,
            "alerts_generated": self.alerts_generated,
            "total_time_ms": total_time_ms,
            "average_event_latency_ms": avg_lat,
            "throughput_eps": round(count / (total_time_ms / 1000.0), 1) if total_time_ms > 0 else 0.0,
        }
