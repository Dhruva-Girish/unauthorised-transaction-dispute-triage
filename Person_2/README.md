# Person 2: AI Agent & Tool Integration

**Component Owner:** Member 2 — Senior AI Agent & LLMOps Engineer  
**System:** Automated Card Dispute Triage and Risk Assessment System

---

## 1. Overview and Responsibilities

Person 2 is responsible for complaint understanding, AI agent orchestration, tool integration, and evidence synthesis:
1. **Gemini & Fallback Classification**: Gemini structured output with deterministic keyword fallback when offline.
2. **Tools Suite**: Transaction retrieval, customer history lookup, duplicate payment window detection, and safe fraud model scoring (consuming Person 1).
3. **LangGraph Agent Workflow**: Stateful `StateGraph` DAG with conditional routing and safety check transitions.
4. **CrewAI Multi-Agent Coordination**: Autonomous 3-agent investigation team (Dispute Investigator, Policy Compliance Officer, Risk Auditor).
5. **RAG Policy Pipeline**: Knowledge base of dispute handling rules (Regulation E, chargeback procedures), sliding window chunker, Chroma/FAISS vector index, and grounded context construction.
6. **Guardrails & Safety Invariant**: Prompt injection detection, output filtering, and enforcement of the non-negotiable rule: **Unauthorized transaction claims must NEVER be automatically dismissed or auto-resolved due to a low ML fraud score**.
7. **TruLens Evaluation**: Automated evaluation of Groundedness, Context Relevance, Faithfulness, Hallucination Rate, Latency, and Token Cost.
8. **Prompt Registry**: Versioned prompt management (`v1.0.0_baseline` vs `v2.0.0_structured_cot`) and comparison analysis.

---

## 2. Integration Contracts

### Upstream: Consuming Person 1 (ML Model Service)
- Person 2 invokes `Person_1.serving.prediction_service.predict_fraud` or queries the Feast online feature store via `Person_2.tools.fraud_scoring_tool.check_fraud_score`.
- If features are absent or ML service is unavailable, Person 2 reports `risk_level: unavailable` and never fabricates scores.

### Downstream: Exposing to Person 3 (Backend & Dashboard)
```python
from Person_2.agents.triage_agent import process_complaint

result = process_complaint(
    complaint_text="I did not make this ₹20,000 transaction. Please investigate.",
    transaction_id="TX1001"
)
```

### Output Schema:
```json
{
  "case_id": "CASE-4F1A8C9B",
  "transaction_id": "TX1001",
  "complaint_category": "unauthorized_transaction",
  "fraud_probability": 0.85,
  "risk_level": "high",
  "priority": "high",
  "evidence_summary": [
    "Transaction record retrieved successfully.",
    "Customer reports that they did not authorize the transaction.",
    "Fraud model returned risk level: high."
  ],
  "recommended_action": "Prioritize fraud investigation and assess appropriate card-protection measures.",
  "requires_human_review": true,
  "status": "under_review",
  "error": null
}
```

---

## 3. Directory Layout

```
Person_2/
├── agents/                  # Authoritative triage agent and master orchestrator
├── classification/          # Gemini structured classifier & keyword fallback
├── tools/                   # Transaction, history, duplicate, and fraud scoring tools
├── workflows/               # Decision trees and routing logic
├── langgraph/               # Stateful LangGraph DAG workflow
├── crewai/                  # CrewAI multi-agent investigation crew
├── rag/                     # Knowledge base, chunker, retriever, RAG pipeline
├── vector_store/            # Chroma and FAISS vector index managers
├── prompts/                 # Prompt registry (v1.0.0 vs v2.0.0) and diff tools
├── evaluation/              # TruLens RAG triad evaluation & benchmark dataset
├── guardrails/              # Injection defense, output filter, safety invariant
├── llm_providers/           # Provider factory (Gemini, Local/Ollama, Fallback)
├── observability/           # Tool execution trace logging & token cost tracker
├── tests/                   # Complete test suite
├── Dockerfile               # Microservice container
├── requirements.txt         # Dependencies
└── README.md                # Component documentation
```

---

## 4. Execution Commands

### Execute Primary LangGraph Triage
```bash
python -c "from agents.triage_agent import process_complaint; print(process_complaint('I did not make this charge.', 'TX1001'))"
```

### Execute CrewAI Multi-Agent Investigation
```bash
python -c "from crewai.fraud_crew import fraud_crew; print(fraud_crew.run_investigation('Charged twice.', 'TX1002'))"
```

### Run TruLens Evaluation Benchmark
```bash
python -c "from evaluation.trulens_evaluator import trulens_evaluator; from agents.triage_agent import process_complaint; print(trulens_evaluator.run_benchmark(process_complaint))"
```

### Run Tests
```bash
pytest tests/ -v
```
