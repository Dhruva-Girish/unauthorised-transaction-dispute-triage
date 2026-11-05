# Operational Runbook: Automated Card Dispute Triage System

## 1. System Overview & Architecture
The Card Dispute Triage System is an asynchronous, event-driven, decision-support platform designed for financial compliance, risk triage, and dispute automation.
- **Backend Port:** 8000 (FastAPI REST)
- **gRPC Port:** 50051 (Binary high-throughput dispute RPC)
- **Dashboard Port:** 8501 (Streamlit Operations Console)
- **Prometheus Port:** 9090 (Scrape endpoint: `/metrics`)
- **Grafana Port:** 3000 (Dashboards: Dispute Triage & SLA Compliance)

---

## 2. Standard Operating Procedures (SOP)

### 2.1 Starting the Services
To start all services in containerized mode:
```bash
docker-compose -f Person_3/docker-compose.yml up -d
```
To run natively in development:
```bash
# Terminal 1: Backend API & gRPC Server
python -m uvicorn Person_3.backend.main:app --port 8000 --reload

# Terminal 2: Streamlit Dashboard
streamlit run Person_3/dashboard/app.py --server.port 8501
```

### 2.2 Health Verification
Verify that all system components and dependencies are healthy:
```bash
curl -f http://localhost:8000/api/v1/health
```
Expected output:
```json
{
  "status": "healthy",
  "database": "connected (wal mode)",
  "queue_pending_jobs": 0,
  "ml_service": "online",
  "circuit_breaker": "CLOSED",
  "uptime_seconds": 124.5
}
```

### 2.3 SLA & Error Budget Monitoring
Check rolling SLA compliance, P50/P95/P99 latency, and error budget:
```bash
curl -f http://localhost:8000/api/v1/sla
```
Expected response:
```json
{
  "availability_pct": 99.95,
  "slo_target_pct": 99.9,
  "is_compliant": true,
  "error_budget_remaining_pct": 95.0,
  "latency_p50_ms": 42.1,
  "latency_p95_ms": 115.4,
  "latency_p99_ms": 180.2
}
```

### 2.4 CLI Application Operations
Inspect cases, run manual triage, or check queue status via CLI:
```bash
# Health check
python Person_3/cli/dispute_cli.py health

# Inspect specific case
python Person_3/cli/dispute_cli.py inspect --id TX1001

# List urgent review cases
python Person_3/cli/dispute_cli.py list --queue urgent_review --limit 10

# Trigger interactive triage
python Person_3/cli/dispute_cli.py triage --text "I see an unauthorized charge of $150 on my statement"
```

---

## 3. Disaster Recovery & Emergency Procedures

### 3.1 LLM Service Outage (Google Gemini API Unreachable)
- **Symptom:** Logs show `Gemini API call failed: Connection timed out` or circuit breaker enters `OPEN` state.
- **System Action:** Circuit breaker trips after 3 consecutive failures. System immediately engages `GracefulDegradationManager` fallback to `KeywordFallbackClassifier` and rule-based policy engine.
- **Safety Guarantee:** Disputed transactions continue to be triaged. No dispute is lost or misclassified. Unauthorized transactions are strictly quarantined to `requires_human_review = True`.
- **Operator Action:** Monitor Gemini API status. Circuit breaker will test recovery after 30 seconds (`HALF-OPEN`). If failure persists, verify `GEMINI_API_KEY` in environment.

### 3.2 Database Lock or IO Congestion
- **Symptom:** Latency P99 exceeds 500ms; database query timeouts.
- **System Action:** SQLite operates in WAL (Write-Ahead Logging) mode, permitting concurrent non-blocking reads during write operations. Case records are asynchronously synchronized to `database/cases.json` backup cache.
- **Operator Action:** Execute checkpoint via:
  ```bash
  sqlite3 Person_3/database/dispute_cases.db "PRAGMA wal_checkpoint(TRUNCATE);"
  ```

### 3.3 Message Queue Backlog Surge
- **Symptom:** Prometheus metric `queue_pending_jobs > 500`.
- **System Action:** Background consumer workers throttle ingestion.
- **Operator Action:** Scale consumer worker threads or switch to persistent Redis broker:
  ```bash
  export QUEUE_BROKER_TYPE=redis
  export REDIS_URL=redis://redis_host:6379/0
  ```

---

## 4. Operational Invariant Verification
Whenever auditing or debugging, ALWAYS ensure:
1. Every complaint categorized as `unauthorized_transaction` has `requires_human_review == True` and `status == 'under_review'`.
2. Fraud ML predictions below 0.15 NEVER resolve or dismiss customer unauthorized disputes.
