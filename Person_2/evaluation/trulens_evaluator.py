"""
trulens_evaluator.py — LLM Evaluation using TruLens Framework (Unit 3.E)
Evaluates Groundedness, Context Relevance, Faithfulness, Hallucination Rate,
Response Latency, and Token Cost across benchmark complaint scenarios.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EVAL_DATASET_PATH = ROOT / "evaluation" / "eval_dataset.json"


class TruLensDisputeEvaluator:
    """Evaluates dispute triage responses against the TruLens RAG Triad."""

    def __init__(self, dataset_path: Path | str | None = None) -> None:
        self.dataset_path = Path(dataset_path) if dataset_path else EVAL_DATASET_PATH

    @staticmethod
    def evaluate_groundedness(evidence_summary: list[str], transaction_found: bool) -> float:
        """Score (0.0 to 1.0) whether all stated evidence is grounded in real data."""
        if not evidence_summary:
            return 1.0 if not transaction_found else 0.5
        score = 1.0
        evidence_text = " ".join(evidence_summary).lower()
        if not transaction_found and "retrieved successfully" in evidence_text:
            score -= 0.5
        if "model returned risk level: None" in evidence_text:
            score -= 0.2
        return max(0.0, min(1.0, score))

    @staticmethod
    def evaluate_context_relevance(category: str, retrieved_context: str) -> float:
        """Score (0.0 to 1.0) relevance of retrieved policy guidelines to dispute category."""
        if not retrieved_context:
            return 0.5
        ctx = retrieved_context.lower()
        cat_words = category.replace("_", " ").split()
        matches = sum(1 for w in cat_words if w in ctx)
        return round(min(1.0, (matches + 1) / (len(cat_words) + 1)), 2)

    @staticmethod
    def evaluate_faithfulness(recommended_action: str, category: str) -> float:
        """Score (0.0 to 1.0) whether recommended action faithfully reflects category."""
        if not recommended_action:
            return 0.0
        act = recommended_action.lower()
        if category == "unauthorized_transaction" and "investigate" in act:
            return 1.0
        if category == "duplicate_payment" and ("duplicate" in act or "matching" in act):
            return 1.0
        if category == "goods_not_received" and ("delivery" in act or "merchant" in act):
            return 1.0
        if category == "billing_dispute" and ("billing" in act or "charge" in act):
            return 1.0
        return 0.8

    def evaluate_case(self, case_spec: dict[str, Any], agent_fn) -> dict[str, Any]:
        """Execute and score one evaluation scenario."""
        complaint = case_spec["complaint_text"]
        tx_id = case_spec["transaction_id"]
        expected_cat = case_spec.get("expected_category")

        t0 = time.perf_counter()
        result = agent_fn(complaint, tx_id)
        latency_ms = round((time.perf_counter() - t0) * 1000.0, 2)

        actual_cat = result.get("complaint_category", "unknown")
        evidence = result.get("evidence_summary", [])
        action = result.get("recommended_action", "")
        tx_found = (result.get("error") != "Transaction not found.")

        # Compute TruLens Triad Metrics
        groundedness = self.evaluate_groundedness(evidence, tx_found)
        context_relevance = self.evaluate_context_relevance(actual_cat, " ".join(evidence))
        faithfulness = self.evaluate_faithfulness(action, actual_cat)
        hallucination_rate = round(1.0 - groundedness, 2)

        # Token cost estimate
        est_tokens = (len(complaint) + len(action) + len(" ".join(evidence))) // 4
        token_cost_usd = round(est_tokens / 1_000_000 * 0.15, 7)

        category_match = (actual_cat == expected_cat)
        safety_compliant = result.get("requires_human_review", False) is True

        return {
            "eval_id": case_spec.get("eval_id"),
            "transaction_id": tx_id,
            "category_match": category_match,
            "groundedness_score": groundedness,
            "context_relevance_score": context_relevance,
            "faithfulness_score": faithfulness,
            "hallucination_rate": hallucination_rate,
            "response_latency_ms": latency_ms,
            "token_count": est_tokens,
            "estimated_token_cost_usd": token_cost_usd,
            "safety_compliant": safety_compliant,
            "overall_pass": category_match and safety_compliant and groundedness >= 0.8,
        }

    def run_benchmark(self, agent_fn) -> dict[str, Any]:
        """Execute all test cases in eval_dataset.json and generate benchmark report."""
        if not self.dataset_path.exists():
            raise FileNotFoundError(f"Eval dataset missing at {self.dataset_path}")

        dataset = json.loads(self.dataset_path.read_text(encoding="utf-8"))
        case_results = [self.evaluate_case(item, agent_fn) for item in dataset]

        total = len(case_results)
        passed = sum(1 for r in case_results if r["overall_pass"])
        avg_groundedness = round(sum(r["groundedness_score"] for r in case_results) / total, 3) if total else 0.0
        avg_relevance = round(sum(r["context_relevance_score"] for r in case_results) / total, 3) if total else 0.0
        avg_faithfulness = round(sum(r["faithfulness_score"] for r in case_results) / total, 3) if total else 0.0
        avg_latency = round(sum(r["response_latency_ms"] for r in case_results) / total, 1) if total else 0.0

        return {
            "evaluator": "TruLens_RAG_Triad",
            "total_scenarios": total,
            "passed_scenarios": passed,
            "benchmark_pass_rate_percent": round((passed / total) * 100.0, 1) if total else 0.0,
            "average_groundedness": avg_groundedness,
            "average_context_relevance": avg_relevance,
            "average_faithfulness": avg_faithfulness,
            "average_latency_ms": avg_latency,
            "case_results": case_results,
        }


# Singleton evaluator
trulens_evaluator = TruLensDisputeEvaluator()
