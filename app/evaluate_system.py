"""
evaluate_system.py — End-to-end evaluation suite for the dispute triage system.

Runs fixed test scenarios from data/test_cases.json against agent.agent.process_complaint.
Validates category classification, risk assessment, evidence synthesis,
error resilience, and policy compliance.
Computes performance benchmarks and writes an evaluation report to data/evaluation_report.json.

Member 3 owns this file.
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

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from agent.agent import process_complaint
from app.agent_ops import compute_agent_ops_metrics, get_case_traces

TEST_CASES_PATH = ROOT / "data" / "test_cases.json"
REPORT_PATH = ROOT / "data" / "evaluation_report.json"


def evaluate_case(tc: dict[str, Any]) -> dict[str, Any]:
    """Execute one test case through process_complaint and evaluate the result."""
    case_id = tc["case_id"]
    tx_id = tc["transaction_id"]
    complaint = tc["complaint_text"]
    expected_cat = tc.get("expected_category")
    scenario = tc.get("scenario", "")

    start = time.perf_counter()
    result = process_complaint(complaint, tx_id)
    latency_ms = round((time.perf_counter() - start) * 1000.0, 2)

    # Validations
    category_ok = (result.get("complaint_category") == expected_cat) if expected_cat else True
    has_action = bool(result.get("recommended_action"))
    human_review_flagged = bool(result.get("requires_human_review"))
    status_ok = result.get("status") in {"under_review", "escalated", "new"}

    if tx_id == "TX-NOT-FOUND":
        has_evidence = isinstance(result.get("evidence_summary"), list)
        no_fabricated_score = (result.get("fraud_probability") is None)
        error_captured = bool(result.get("error"))
    else:
        has_evidence = isinstance(result.get("evidence_summary"), list) and len(result.get("evidence_summary", [])) > 0
        no_fabricated_score = True
        error_captured = True

    passed = (
        category_ok
        and has_evidence
        and has_action
        and human_review_flagged
        and status_ok
        and no_fabricated_score
        and error_captured
    )

    return {
        "test_case_id": case_id,
        "scenario": scenario,
        "transaction_id": tx_id,
        "complaint_snippet": complaint[:60] + "...",
        "actual_case_id": result.get("case_id"),
        "complaint_category": result.get("complaint_category"),
        "expected_category": expected_cat,
        "category_matched": category_ok,
        "fraud_probability": result.get("fraud_probability"),
        "risk_level": result.get("risk_level"),
        "priority": result.get("priority"),
        "status": result.get("status"),
        "requires_human_review": human_review_flagged,
        "evidence_count": len(result.get("evidence_summary", [])),
        "has_recommended_action": has_action,
        "latency_ms": latency_ms,
        "passed": passed,
        "error": result.get("error"),
    }


def run_evaluation() -> dict[str, Any]:
    """Run all test scenarios, print CLI summary, and save evaluation report."""
    if not TEST_CASES_PATH.exists():
        raise FileNotFoundError(f"Test cases file not found at {TEST_CASES_PATH}")

    test_cases: list[dict[str, Any]] = json.loads(TEST_CASES_PATH.read_text(encoding="utf-8"))

    print("\n" + "=" * 80)
    print("  CARD DISPUTE TRIAGE SYSTEM — END-TO-END EVALUATION")
    print("  Evaluating ML System Design & Agent Ops Integration (Member 3)")
    print("=" * 80)

    evaluated_cases = []
    for tc in test_cases:
        res = evaluate_case(tc)
        evaluated_cases.append(res)

        status_tag = "[PASS]" if res["passed"] else "[FAIL]"
        print(f"\n{status_tag} {tc['case_id']} | TX: {tc['transaction_id']}")
        print(f"  Scenario:   {tc.get('scenario')}")
        print(f"  Category:   {res['complaint_category']} (Expected: {res['expected_category']})")
        print(f"  Priority:   {res['priority']} | Status: {res['status']} | Human Review: {res['requires_human_review']}")
        print(f"  Risk Level: {res['risk_level']} | Latency: {res['latency_ms']} ms")
        if res.get("error"):
            print(f"  Note/Error: {res['error']}")

    total = len(evaluated_cases)
    passed = sum(1 for c in evaluated_cases if c["passed"])
    accuracy = round((passed / total) * 100.0, 1) if total else 0.0

    ops_metrics = compute_agent_ops_metrics()

    print("\n" + "=" * 80)
    print("  EVALUATION SUMMARY")
    print("=" * 80)
    print(f"  Total Test Cases:    {total}")
    print(f"  Passed:              {passed} / {total} ({accuracy}%)")
    print(f"  Average Latency:     {round(sum(c['latency_ms'] for c in evaluated_cases) / total, 1)} ms")
    print(f"  Historical Cases:    {ops_metrics['total_cases']}")
    print(f"  System Success Rate: {ops_metrics['success_rate']}%")
    print("=" * 80 + "\n")

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_test_cases": total,
        "passed_test_cases": passed,
        "test_pass_rate": accuracy,
        "evaluation_cases": evaluated_cases,
        "agent_ops_metrics": ops_metrics,
    }

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Detailed evaluation report saved to: {REPORT_PATH}\n")

    return report


if __name__ == "__main__":
    run_evaluation()
