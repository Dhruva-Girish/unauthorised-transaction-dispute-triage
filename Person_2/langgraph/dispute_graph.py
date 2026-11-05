"""
dispute_graph.py — LangGraph Agent Workflow Orchestration (Unit 4.A)
Implements a stateful Directed Acyclic Graph (DAG) for card dispute triage
with explicit node boundaries, conditional routing, tool executions, and safety checks.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any
from uuid import uuid4

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .state import DisputeState
from classification.gemini_classifier import GeminiClassifier
from classification.keyword_fallback import KeywordFallbackClassifier
from tools.transaction_tool import get_transaction
from tools.duplicate_tool import check_duplicate_transactions
from tools.history_tool import get_customer_history
from tools.fraud_scoring_tool import check_fraud_score
from rag.rag_pipeline import rag_engine
from guardrails.injection_defense import InjectionDefenseGuardrail
from guardrails.safety_checker import SafetyChecker
from observability.trace_logger import agent_logger

try:
    from langgraph.graph import StateGraph, END
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    END = "__end__"

_gemini_classifier = GeminiClassifier()
_injection_guard = InjectionDefenseGuardrail()


# ── Node Implementations ───────────────────────────────────────────────────

def node_classify(state: DisputeState) -> dict[str, Any]:
    """Node 1: Scan for prompt injection and classify complaint."""
    t0 = time.perf_counter()
    text = state.get("complaint_text", "")
    tx_id = state.get("transaction_id", "")

    # Injection Guardrail check
    injection_res = _injection_guard.inspect(text)
    clean_text = injection_res["sanitized_text"]

    clf_res = _gemini_classifier.classify(clean_text, tx_id)
    dur = round((time.perf_counter() - t0) * 1000.0, 2)

    agent_logger.log_event(
        case_id=state.get("case_id", "UNKNOWN"),
        event_type="classification_completed",
        details=clf_res,
        duration_ms=dur,
    )

    steps = state.get("execution_steps", []) + ["classify_complaint"]
    return {
        "complaint_category": clf_res["category"],
        "classification_confidence": clf_res.get("confidence", 0.9),
        "classifier_provider": clf_res.get("provider", "keyword_classifier"),
        "execution_steps": steps,
    }


def node_lookup_transaction(state: DisputeState) -> dict[str, Any]:
    """Node 2: Retrieve transaction and customer history from ledger."""
    t0 = time.perf_counter()
    tx_id = state.get("transaction_id", "")
    tx = get_transaction(tx_id)
    dur = round((time.perf_counter() - t0) * 1000.0, 2)

    found = tx is not None
    cust_id = tx.get("customer_id") if tx else None
    history = get_customer_history(cust_id, exclude_transaction_id=tx_id) if cust_id else []

    agent_logger.log_tool_call(
        case_id=state.get("case_id", "UNKNOWN"),
        tool_name="get_transaction",
        input_args={"transaction_id": tx_id},
        output_result="found" if found else "not_found",
        duration_ms=dur,
        success=found,
    )

    steps = state.get("execution_steps", []) + ["lookup_transaction"]
    return {
        "transaction": tx,
        "transaction_found": found,
        "customer_id": cust_id,
        "customer_history": history,
        "execution_steps": steps,
    }


def node_check_duplicates(state: DisputeState) -> dict[str, Any]:
    """Node 3: Detect potential duplicate payments in window."""
    t0 = time.perf_counter()
    tx_id = state.get("transaction_id", "")
    duplicates = check_duplicate_transactions(tx_id, window_minutes=10)
    dur = round((time.perf_counter() - t0) * 1000.0, 2)

    agent_logger.log_tool_call(
        case_id=state.get("case_id", "UNKNOWN"),
        tool_name="check_duplicate_transactions",
        input_args={"transaction_id": tx_id},
        output_result=f"{len(duplicates)} duplicates found",
        duration_ms=dur,
        success=True,
    )

    steps = state.get("execution_steps", []) + ["check_duplicates"]
    return {
        "duplicate_matches": duplicates,
        "execution_steps": steps,
    }


def node_retrieve_policy_rag(state: DisputeState) -> dict[str, Any]:
    """Node 4: Retrieve relevant banking guidelines and regulations via RAG."""
    t0 = time.perf_counter()
    complaint = state.get("complaint_text", "")
    category = state.get("complaint_category", "unknown")

    context = rag_engine.build_grounded_context(
        complaint_text=complaint,
        category=category,
        transaction=state.get("transaction"),
    )
    dur = round((time.perf_counter() - t0) * 1000.0, 2)

    steps = state.get("execution_steps", []) + ["retrieve_policy_rag"]
    return {
        "retrieved_policies": context["retrieved_policies"],
        "execution_steps": steps,
    }


def node_evaluate_fraud(state: DisputeState) -> dict[str, Any]:
    """Node 5: Score fraud probability using Person 1's ML model."""
    t0 = time.perf_counter()
    tx = state.get("transaction")
    fraud_res = check_fraud_score(tx) if tx else {}
    dur = round((time.perf_counter() - t0) * 1000.0, 2)

    agent_logger.log_tool_call(
        case_id=state.get("case_id", "UNKNOWN"),
        tool_name="check_fraud_score",
        input_args={"transaction_id": state.get("transaction_id")},
        output_result=fraud_res.get("risk_level", "unavailable"),
        duration_ms=dur,
        success=fraud_res.get("fraud_probability") is not None,
    )

    steps = state.get("execution_steps", []) + ["evaluate_fraud"]
    return {
        "fraud_probability": fraud_res.get("fraud_probability"),
        "risk_level": fraud_res.get("risk_level", "unavailable"),
        "execution_steps": steps,
    }


def node_synthesize_decision(state: DisputeState) -> dict[str, Any]:
    """Node 6: Synthesize evidence and generate prioritized recommendation."""
    tx_found = state.get("transaction_found", False)
    tx_id = state.get("transaction_id", "")
    category = state.get("complaint_category", "unknown")
    risk = state.get("risk_level", "unavailable")
    prob = state.get("fraud_probability")
    duplicates = state.get("duplicate_matches", [])

    if not tx_found:
        return {
            "priority": "review_required",
            "recommended_action": "Request valid transaction information and review the complaint.",
            "evidence_summary": [],
            "requires_human_review": True,
            "status": "under_review",
            "error": "Transaction not found.",
            "execution_steps": state.get("execution_steps", []) + ["synthesize_decision"],
        }

    evidence = ["Transaction record retrieved successfully."]

    if category == "unauthorized_transaction":
        evidence.append("Customer reports that they did not authorize the transaction.")
        if risk == "high":
            priority = "high"
            action = "Prioritize fraud investigation and assess appropriate card-protection measures."
        else:
            priority = "review_required"
            action = "Investigate the unauthorized-transaction claim regardless of the model score."

    elif category == "duplicate_payment":
        if duplicates:
            evidence.append(f"{len(duplicates)} possible matching transaction(s) found.")
            priority = "medium"
            action = "Review matching transactions and verify whether a duplicate charge occurred."
        else:
            priority = "medium"
            action = "Review payment records and request additional evidence if needed."

    elif category == "goods_not_received":
        priority = "medium"
        action = "Request order and delivery evidence and route the case for merchant-dispute review."

    elif category == "billing_dispute":
        priority = "medium"
        action = "Review the charge and relevant billing records."

    else:
        priority = "review_required"
        action = "Clarify the complaint and route it for appropriate review."

    if prob is not None:
        evidence.append(f"Fraud model returned risk level: {risk}.")
    else:
        evidence.append("Fraud score is unavailable.")

    # Append RAG policy note
    policies = state.get("retrieved_policies", [])
    if policies:
        evidence.append(f"Policy Reference: {policies[0][:100]}...")

    steps = state.get("execution_steps", []) + ["synthesize_decision"]
    return {
        "priority": priority,
        "recommended_action": action,
        "evidence_summary": evidence,
        "requires_human_review": True,
        "status": "under_review",
        "error": None,
        "execution_steps": steps,
    }


def node_enforce_safety(state: DisputeState) -> dict[str, Any]:
    """Node 7: Guardrail enforcement — ensure non-dismissal invariant."""
    hr = state.get("requires_human_review", True)
    status = state.get("status", "under_review")
    cat = state.get("complaint_category", "unknown")
    risk = state.get("risk_level", "unavailable")
    prob = state.get("fraud_probability")

    hr_enforced, status_enforced, notes = SafetyChecker.enforce_unauthorized_transaction_safety(
        complaint_category=cat,
        fraud_probability=prob,
        risk_level=risk,
        current_status=status,
        requires_human_review=hr,
    )

    steps = state.get("execution_steps", []) + ["enforce_safety"]
    return {
        "requires_human_review": hr_enforced,
        "status": status_enforced,
        "execution_steps": steps,
    }


# ── LangGraph Workflow Construction ────────────────────────────────────────

def build_langgraph_dispute_workflow():
    """Construct and compile the stateful LangGraph dispute workflow."""
    if not LANGGRAPH_AVAILABLE:
        return None

    workflow = StateGraph(DisputeState)

    workflow.add_node("classify", node_classify)
    workflow.add_node("lookup_tx", node_lookup_transaction)
    workflow.add_node("check_duplicates", node_check_duplicates)
    workflow.add_node("rag_policies", node_retrieve_policy_rag)
    workflow.add_node("fraud_scoring", node_evaluate_fraud)
    workflow.add_node("synthesize", node_synthesize_decision)
    workflow.add_node("safety_enforcer", node_enforce_safety)

    workflow.set_entry_point("classify")
    workflow.add_edge("classify", "lookup_tx")

    # Conditional routing after transaction lookup
    def route_after_lookup(state: DisputeState) -> str:
        if not state.get("transaction_found", False):
            return "synthesize"
        category = state.get("complaint_category")
        if category == "duplicate_payment":
            return "check_duplicates"
        return "rag_policies"

    workflow.add_conditional_edges(
        "lookup_tx",
        route_after_lookup,
        {
            "synthesize": "synthesize",
            "check_duplicates": "check_duplicates",
            "rag_policies": "rag_policies",
        },
    )

    workflow.add_edge("check_duplicates", "rag_policies")
    workflow.add_edge("rag_policies", "fraud_scoring")
    workflow.add_edge("fraud_scoring", "synthesize")
    workflow.add_edge("synthesize", "safety_enforcer")
    workflow.add_edge("safety_enforcer", END)

    return workflow.compile()


compiled_dispute_graph = build_langgraph_dispute_workflow()


def run_langgraph_workflow(complaint_text: str, transaction_id: str) -> dict[str, Any]:
    """Execute the compiled LangGraph workflow or deterministic fallback DAG."""
    case_id = f"CASE-{uuid4().hex[:8].upper()}"
    start = time.perf_counter()

    initial_state: DisputeState = {
        "case_id": case_id,
        "complaint_text": complaint_text,
        "transaction_id": transaction_id,
        "execution_steps": [],
    }

    if compiled_dispute_graph is not None:
        try:
            final_state = compiled_dispute_graph.invoke(initial_state)
            total_latency = round((time.perf_counter() - start) * 1000.0, 2)
            final_state["total_latency_ms"] = total_latency
            return final_state
        except Exception:
            pass

    # Deterministic sequential fallback execution if graph execution encounters runtime errors
    s1 = node_classify(initial_state)
    st = {**initial_state, **s1}
    s2 = node_lookup_transaction(st)
    st.update(s2)

    if st.get("transaction_found"):
        if st.get("complaint_category") == "duplicate_payment":
            st.update(node_check_duplicates(st))
        st.update(node_retrieve_policy_rag(st))
        st.update(node_evaluate_fraud(st))

    st.update(node_synthesize_decision(st))
    st.update(node_enforce_safety(st))
    st["total_latency_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
    return st
