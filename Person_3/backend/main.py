"""
main.py — Master FastAPI Application Server (Unit 1.C, 2.B, 4.B)
Integrates Person 1 ML Service, Person 2 Agent Workflow, and Person 3 Backend Infrastructure.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.routers.triage_router import router as triage_router
from api.routers.cases_router import router as cases_router
from api.routers.health_router import router as health_router
from api.routers.metrics_router import router as metrics_router
from message_queue.consumer_worker import queue_worker
from webhooks.webhook_manager import webhook_manager
from observability.metrics_collector import record_request_metric

app = FastAPI(
    title="Card Dispute Triage & Risk Assessment Service",
    description="Automated ML-powered fraud scoring and AI-agent dispute triage backend.",
    version="2.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def telemetry_middleware(request: Request, call_next):
    """Timing and Prometheus metrics middleware."""
    t0 = time.perf_counter()
    response = await call_next(request)
    duration_ms = round((time.perf_counter() - t0) * 1000.0, 2)
    response.headers["X-Response-Time-Ms"] = str(duration_ms)

    record_request_metric(
        method=request.method,
        endpoint=request.url.path,
        status_code=response.status_code,
    )
    return response


# Include routers
app.include_router(triage_router)
app.include_router(cases_router)
app.include_router(health_router)
app.include_router(metrics_router)


# Webhook registration endpoints
@app.post("/api/v1/webhooks", tags=["Webhooks"])
def register_webhook_endpoint(target_url: str, events: list[str], secret: str | None = None):
    """Register an outgoing webhook destination."""
    return webhook_manager.register_webhook(target_url, events, secret)


@app.get("/api/v1/webhooks", tags=["Webhooks"])
def list_webhooks_endpoint():
    """List registered webhooks."""
    return {"webhooks": webhook_manager.list_subscriptions()}


@app.on_event("startup")
def on_startup():
    """Start background queue worker on application boot and sync metrics."""
    queue_worker.start()
    print("Background message queue consumer worker started.")
    try:
        from database.case_repository import case_repo
        from observability.metrics_collector import set_active_cases_metric
        from collections import Counter
        cases = case_repo.list_cases(limit=1000)
        status_counts = Counter(c.get("status", "under_review") for c in cases)
        for st_name, count_val in status_counts.items():
            set_active_cases_metric(st_name, count_val)
        if not status_counts:
            set_active_cases_metric("under_review", 0)
    except Exception as exc:
        print(f"Metrics startup sync notice: {exc}")


@app.on_event("shutdown")
def on_shutdown():
    """Stop worker on application shutdown."""
    queue_worker.stop()


@app.get("/")
def root_index():
    return {
        "service": "Card Dispute Triage and Risk Assessment System",
        "documentation": "/docs",
        "health": "/api/v1/health",
        "metrics": "/metrics",
        "sla": "/api/v1/sla",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=False)
