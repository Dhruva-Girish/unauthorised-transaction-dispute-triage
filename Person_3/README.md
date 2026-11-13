# Person 3: Integration, AgentOps, Observability & Dashboard

## Overview
Person 3 is responsible for the overall system integration, backend APIs, distributed observability, operational reliability, security controls, gRPC interfaces, and interactive investigator dashboard.

## Key Modules & Responsibilities
- **`backend/` & `api/`:** Production FastAPI application (`main.py`) exposing REST endpoints:
  - `POST /api/v1/triage`: Synchronous end-to-end complaint triage.
  - `POST /api/v1/async-triage`: Asynchronous queuing for high-throughput spikes.
  - `GET /api/v1/cases`: Multi-criteria case filtering (status, queue, priority, customer).
  - `GET /api/v1/health`: System health status and dependency checks.
  - `GET /api/v1/sla`: Real-time SLA/SLO compliance and latency percentiles.
  - `GET /metrics`: Standard Prometheus metrics exposition.
- **`database/`:** SQLite database with WAL (Write-Ahead Logging) mode, ACID transactions, relational schema, and backup cache synchronization (`case_repository.py`).
- **`grpc/`:** High-performance binary RPC server (`grpc_server.py`) and client (`grpc_client.py`) on port 50051.
- **`cli/`:** Command-line management tool (`dispute_cli.py`) supporting triage, inspection, queue listing, and batch processing.
- **`webhooks/`:** Outbound event notification system with HMAC-SHA256 signature verification and automatic retry dispatcher.
- **`message_queue/`:** Asynchronous queue broker (`queue_broker.py`) and background worker daemon (`consumer_worker.py`).
- **`reliability/`:** Enterprise resilience utilities:
  - `circuit_breaker.py`: 3-state circuit breaker (CLOSED, OPEN, HALF-OPEN).
  - `retry_handler.py`: Exponential backoff with jitter.
  - `graceful_degradation.py`: Fallback manager for external service outages.
- **`security/`:**
  - `auth.py`: API key / Bearer token authentication middleware.
  - `rate_limiter.py`: Sliding token-bucket rate limiter.
- **`telemetry/` & `observability/`:**
  - `otel_tracer.py`: OpenTelemetry distributed tracing spans.
  - `metrics_collector.py`: Prometheus request counters, latency histograms, and queue gauges.
  - `sla_monitor.py`: Rolling SLA/SLO calculator (P50, P95, P99).
- **`dashboard/`:** Streamlit interactive operational dashboard (`app.py`):
  - Live Triage Console with demo presets.
  - Human Investigation Queue & Case Detail Inspector.
  - System Observability & SLA Compliance Gauges.
  - Feast Online Feature Store & Data Drift Inspector.
- **`load_testing/`:** Locust load testing suite (`locustfile.py`) measuring throughput, error rate, and P50/P95 latencies.

## Running Tests
```bash
pytest Person_3/tests/ -v
```

## Running Services
```bash
# FastAPI Backend
python -m uvicorn Person_3.backend.main:app --host 0.0.0.0 --port 8000

# Streamlit Dashboard
streamlit run Person_3/dashboard/app.py
```
