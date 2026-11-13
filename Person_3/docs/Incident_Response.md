# Incident Response Guide: Card Dispute Triage System

## Severity Levels & Triage Framework

| Severity | Definition | Response Target | Escalation Contact |
|---|---|---|---|
| **SEV-1 (Critical)** | Core triage pipeline down; customer unauthorized dispute auto-dismissed or rejected. | < 15 minutes | Lead Architect, Compliance Officer |
| **SEV-2 (Major)** | Backend API latency P95 > 1,500ms; external LLM outage with degraded fallback. | < 30 minutes | On-call Backend / ML Engineer |
| **SEV-3 (Minor)** | Webhook delivery retry surge; background queue worker lag > 200 cases. | < 2 hours | Systems Administrator |
| **SEV-4 (Low)** | Non-blocking dashboard rendering glitch; cosmetic log discrepancy. | Next Business Day | Frontend / Dashboard Dev |

---

## SEV-1 Incident Playbook: Safety Invariant Breach Detection

### Trigger
Alert fired: `UnauthorizedDisputeDismissedRuleTriggered` or auditor flag where `requires_human_review == False` on `unauthorized_transaction`.

### Mitigation Steps
1. **Immediate Quarantine:**
   Lock automated resolution and run database patch:
   ```bash
   python -c "
   from Person_3.database.case_repository import CaseRepository
   repo = CaseRepository()
   cases = repo.list_cases(category='unauthorized_transaction', limit=1000)
   for c in cases:
       if not c.get('requires_human_review') or c.get('status') == 'resolved':
           repo.update_case_status(c['dispute_id'], 'under_review', 'Emergency compliance patch')
   print('Quarantined invalidly resolved cases.')
   "
   ```
2. **Inspect Guardrail Logs:**
   Verify `Person_2/guardrails/safety_checker.py` and `Person_2/guardrails/output_filter.py`. Check if prompt injection bypassed classifier.
3. **Notify Compliance:**
   Log incident timeline and export case audit trail for risk auditor review.

---

## SEV-2 Incident Playbook: External LLM / gRPC Failure

### Trigger
Alert fired: `CircuitBreakerTrippedOpen` (Gemini API 500 error / 429 quota exhaustion).

### Mitigation Steps
1. **Verify Circuit State:**
   Check `/api/v1/health` for `circuit_breaker: "OPEN"`.
2. **Confirm Fallback Operation:**
   Inspect `agent_ops.jsonl` to ensure `KeywordFallbackClassifier` has engaged seamlessly.
3. **Verify Zero Data Loss:**
   Confirm incoming dispute complaints are stored in queue and assigned priority.
4. **Gradual Recovery:**
   Once external API status is operational, trigger manual half-open reset:
   ```bash
   python -c "from Person_3.reliability.circuit_breaker import get_circuit_breaker; get_circuit_breaker('llm').reset()"
   ```
