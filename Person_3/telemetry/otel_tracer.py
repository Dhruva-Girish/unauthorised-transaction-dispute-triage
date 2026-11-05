"""
otel_tracer.py — OpenTelemetry Distributed Tracing (Unit 2.C)
Traces request flow across FastAPI routes, Agent execution, Tools, and Database layers.
"""

from __future__ import annotations

import contextlib
from typing import Generator, Any

try:
    from opentelemetry import trace
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
    from opentelemetry.sdk.resources import Resource

    OTEL_AVAILABLE = True
    provider = TracerProvider(resource=Resource.create({"service.name": "card-dispute-triage-backend"}))
    trace.set_tracer_provider(provider)
    tracer = trace.get_tracer("dispute.triage.tracer")
except Exception:
    OTEL_AVAILABLE = False
    tracer = None


@contextlib.contextmanager
def trace_span(span_name: str, attributes: dict[str, Any] | None = None) -> Generator[Any, None, None]:
    """Context manager creating an OpenTelemetry trace span."""
    if OTEL_AVAILABLE and tracer is not None:
        with tracer.start_as_current_span(span_name) as span:
            if attributes:
                for k, v in attributes.items():
                    span.set_attribute(str(k), str(v))
            yield span
    else:
        # Fallback dummy span
        yield None
