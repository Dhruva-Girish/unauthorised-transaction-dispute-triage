"""
test_trulens.py — Tests for TruLens RAG Triad Evaluation (Unit 3.E)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from evaluation.trulens_evaluator import trulens_evaluator
from agents.triage_agent import process_complaint


def test_trulens_groundedness_calculation():
    # Legitimate evidence
    g1 = trulens_evaluator.evaluate_groundedness(["Transaction record retrieved successfully."], transaction_found=True)
    assert g1 == 1.0

    # Hallucinated evidence (asserted found when tx was not found)
    g2 = trulens_evaluator.evaluate_groundedness(["Transaction record retrieved successfully."], transaction_found=False)
    assert g2 < 1.0


def test_trulens_context_relevance():
    rel = trulens_evaluator.evaluate_context_relevance(
        category="unauthorized_transaction",
        retrieved_context="Policy guidelines regarding unauthorized card transactions and fraud.",
    )
    assert rel >= 0.7


def test_trulens_benchmark_execution():
    report = trulens_evaluator.run_benchmark(process_complaint)
    assert report["total_scenarios"] == 5
    assert report["passed_scenarios"] >= 4
    assert report["benchmark_pass_rate_percent"] >= 80.0
    assert report["average_groundedness"] >= 0.8
