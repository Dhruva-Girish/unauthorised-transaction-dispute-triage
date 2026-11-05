"""
app.py — Streamlit Case Management & Agent Ops Dashboard for Dispute Triage.

Clean, uncluttered, and 100% compatible with both Light and Dark modes.
Provides:
  1. Dispute Submission & AI Triage (Clean, Minimalist View)
  2. Case Management Review Queue
  3. Agent Ops & System Metrics
  4. ML Fraud Model Diagnostics
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agent.agent import process_complaint
from agent.case_store import load_cases
from app.agent_ops import (
    load_raw_logs,
    get_case_traces,
    compute_agent_ops_metrics,
    AgentTrace,
)

# ── Streamlit Page Configuration ───────────────────────────────────────────
st.set_page_config(
    page_title="Card Dispute Triage",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme-Safe Custom CSS (No hardcoded backgrounds or text colors) ────────
st.markdown(
    """
    <style>
    /* Clean container spacing */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    h1, h2, h3 { margin-bottom: 0.5rem; }
    .stAlert { margin-top: 0.5rem; margin-bottom: 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ── Category and Status Helpers ─────────────────────────────────────────────
CATEGORY_NAMES = {
    "unauthorized_transaction": "Unauthorized Transaction",
    "duplicate_payment": "Duplicate Payment",
    "goods_not_received": "Goods Not Received",
    "billing_dispute": "Billing Dispute",
    "other": "Other",
    "unknown": "Unknown / Unclassified",
}

STATUS_NAMES = {
    "under_review": "Under Review",
    "escalated": "Escalated",
    "resolved": "Resolved",
    "new": "New Case",
}

PRIORITY_NAMES = {
    "high": "High Priority",
    "medium": "Medium Priority",
    "review_required": "Review Required",
    "low": "Low Priority",
}

PRESETS = {
    "-- Select a Quick Scenario Preset (Optional) --": {
        "text": "",
        "tx": "TX1001",
    },
    "🚨 Unauthorized ₹20,000 at 2:15 AM": {
        "text": "I did not make this ₹20,000 payment to an online merchant at 2:15 AM. My card was with me. Please investigate immediately.",
        "tx": "TX1001",
    },
    "🔁 Duplicate Restaurant Charge ₹1,200": {
        "text": "I was charged twice for the same dinner at Example Restaurant. Both charges appeared at almost the same time.",
        "tx": "TX1002",
    },
    "📦 Goods Never Received": {
        "text": "I paid for headphones online 3 weeks ago, but the merchant never delivered them and the tracking link is dead.",
        "tx": "TX1002",
    },
    "❓ Unknown Charge / Missing Transaction ID": {
        "text": "I see an unauthorized charge on my card statement that I did not authorize.",
        "tx": "TX-NOT-FOUND",
    },
}

# ── Sidebar Navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("💳 Dispute Triage")
    st.caption("AI-Powered Card Complaint Resolution")
    st.divider()

    selected_view = st.radio(
        "Navigation",
        [
            "📝 Triage Dispute",
            "📋 Case Queue",
            "📊 Agent Ops & Telemetry",
            "🧠 ML Fraud Model",
        ],
        index=0,
    )

    st.divider()
    st.caption("**Safety Guarantee**: Unauthorized claims are never auto-dismissed based on ML scores alone.")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 1: Submit & Triage Complaint (Clean & Minimalist)
# ════════════════════════════════════════════════════════════════════════════
if selected_view == "📝 Triage Dispute":
    st.title("Card Dispute Triage")
    st.caption("Submit customer complaints for AI classification, ML risk scoring, and evidence-based investigation triage.")

    with st.container(border=True):
        # Clean dropdown preset selector
        selected_preset = st.selectbox(
            "Quick Scenario Presets (Optional)",
            list(PRESETS.keys()),
            index=0,
        )
        preset_info = PRESETS[selected_preset]

        with st.form("triage_form"):
            col_tx, _ = st.columns([1, 2])
            with col_tx:
                default_tx = preset_info["tx"] if preset_info["tx"] else "TX1001"
                transaction_id = st.text_input(
                    "Transaction ID",
                    value=default_tx,
                    help="Transaction identifier from statement (e.g. TX1001, TX1002).",
                )

            default_text = preset_info["text"] if preset_info["text"] else "I did not authorize this ₹20,000 transaction on my statement."
            complaint_text = st.text_area(
                "Customer Complaint",
                value=default_text,
                height=100,
                help="Natural language dispute submitted by the cardholder.",
            )

            submitted = st.form_submit_button(
                "🔍 Run AI Triage",
                type="primary",
                use_container_width=True,
            )

    if submitted and complaint_text.strip():
        with st.spinner("AI Agent analyzing complaint and calculating risk..."):
            with AgentTrace(complaint_text.strip(), transaction_id.strip()) as trace:
                result = process_complaint(complaint_text.strip(), transaction_id.strip())
                trace.set_result(result)

        st.session_state["latest_result"] = result
        st.session_state["latest_latency"] = trace.duration_ms

    latest_result = st.session_state.get("latest_result")
    latency_val = st.session_state.get("latest_latency", 0.0)

    if latest_result:
        st.subheader("📋 Triage Recommendation")

        cat = latest_result.get("complaint_category", "unknown")
        cat_display = CATEGORY_NAMES.get(cat, cat.replace("_", " ").title())
        prio = latest_result.get("priority", "review_required")
        prio_display = PRIORITY_NAMES.get(prio, prio.replace("_", " ").title())
        status = latest_result.get("status", "under_review")
        status_display = STATUS_NAMES.get(status, status.replace("_", " ").title())
        risk = latest_result.get("risk_level", "unavailable").capitalize()
        prob = latest_result.get("fraud_probability")
        prob_str = f"{prob:.1%}" if prob is not None else "N/A"
        requires_hr = latest_result.get("requires_human_review", True)
        case_id = latest_result.get("case_id", "N/A")

        # 4 clean native Streamlit metrics (Adapts to both Light & Dark themes natively)
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown("**Dispute Category**")
            st.markdown(f"### {cat_display}")
        with m2:
            st.metric("Priority Queue", prio_display)
        with m3:
            st.metric("ML Fraud Risk", prob_str, delta=risk, delta_color="off")
        with m4:
            st.metric("Human Review", "Required" if requires_hr else "Auto-Resolved")

        # Action banner
        rec_action = latest_result.get("recommended_action", "No action specified.")
        if requires_hr:
            st.warning(f"⚠️ **Recommended Action:** {rec_action}")
        else:
            st.success(f"✅ **Recommended Action:** {rec_action}")

        if latest_result.get("error"):
            st.error(f"**Notice:** {latest_result['error']}")

        # Clean evidence display
        evidence_list = latest_result.get("evidence_summary", [])
        if evidence_list:
            with st.container(border=True):
                st.markdown("**Evidence & Findings:**")
                for ev in evidence_list:
                    if "Policy Reference:" in ev or "Definition:" in ev:
                        st.caption(f"📜 {ev}")
                    else:
                        st.markdown(f"• {ev}")

        # Developer / Audit traces in a collapsible section (Keeps UI clean for investigators)
        with st.expander("🔍 Technical Audit & Agent Trace", expanded=False):
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown(f"**Case Reference:** `{case_id}`")
                st.markdown(f"**Transaction ID:** `{latest_result.get('transaction_id')}`")
                st.markdown(f"**Execution Latency:** `{latency_val} ms`")
            with t_col2:
                st.markdown(f"**Case Status:** `{status_display}`")
                st.markdown(f"**Human Review Flag:** `{requires_hr}`")

            # Timeline steps from logs
            traces = get_case_traces()
            case_events = traces.get(case_id, [])
            if case_events:
                st.markdown("**Execution Pipeline Steps:**")
                step_labels = [ev.get("event_type", "step").replace("_", " ").title() for ev in case_events]
                st.markdown(" ➔ ".join([f"`{s}`" for s in step_labels]))

            st.json(latest_result)


# ════════════════════════════════════════════════════════════════════════════
# VIEW 2: Case Management Queue
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "📋 Case Queue":
    st.title("Case Management Queue")
    st.caption("Active dispute cases triaged and persisted.")

    cases = load_cases()

    if not cases:
        st.info("No cases currently in the database. Submit a complaint to create the first case.")
    else:
        # Filter controls
        f1, f2, f3 = st.columns(3)
        with f1:
            all_statuses = ["All"] + sorted({c.get("status", "unknown") for c in cases})
            sel_status = st.selectbox("Status", all_statuses)
        with f2:
            all_categories = ["All"] + sorted({c.get("complaint_category", "unknown") for c in cases})
            sel_cat = st.selectbox("Category", all_categories)
        with f3:
            all_priorities = ["All"] + sorted({c.get("priority", "unknown") for c in cases})
            sel_prio = st.selectbox("Priority", all_priorities)

        # Apply filters
        filtered_cases = [
            c for c in cases
            if (sel_status == "All" or c.get("status") == sel_status)
            and (sel_cat == "All" or c.get("complaint_category") == sel_cat)
            and (sel_prio == "All" or c.get("priority") == sel_prio)
        ]

        st.caption(f"Showing **{len(filtered_cases)}** of **{len(cases)}** total cases.")

        for c in reversed(filtered_cases):
            cid = c.get("case_id", "UNKNOWN")
            txid = c.get("transaction_id", "N/A")
            cat = c.get("complaint_category", "unknown")
            cat_label = CATEGORY_NAMES.get(cat, cat)
            prio = (c.get("priority") or "review_required").upper()
            status = (c.get("status") or "under_review").upper()

            with st.expander(f"📁 **{cid}** — {cat_label} | TX: {txid} | **[{prio}]** Status: {status}"):
                c_col1, c_col2 = st.columns([1.5, 1])
                with c_col1:
                    st.markdown("**Recommended Action:**")
                    st.info(c.get("recommended_action", "Review claim."))
                    ev_items = c.get("evidence_summary", [])
                    if ev_items:
                        st.markdown("**Evidence:**")
                        for ev in ev_items:
                            if "Policy Reference:" in ev:
                                st.caption(f"📜 {ev}")
                            else:
                                st.markdown(f"• {ev}")
                with c_col2:
                    st.markdown(f"**Risk Level:** `{c.get('risk_level', 'unavailable')}`")
                    prob = c.get('fraud_probability')
                    prob_str = f"{prob:.1%}" if prob is not None else "N/A"
                    st.markdown(f"**Fraud Probability:** `{prob_str}`")
                    st.markdown(f"**Requires Human Review:** `{c.get('requires_human_review')}`")
                    if c.get("error"):
                        st.error(f"Error: {c['error']}")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 3: Agent Ops & Observability
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "📊 Agent Ops & Telemetry":
    st.title("Agent Ops & Telemetry")
    st.caption("Operational metrics and execution telemetry.")

    metrics = compute_agent_ops_metrics()

    # KPI Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Cases", metrics.get("total_cases", 0))
    with m2:
        st.metric("Total Events", metrics.get("total_events", 0))
    with m3:
        st.metric("Success Rate", f"{metrics.get('success_rate', 100)}%")
    with m4:
        st.metric("Avg Latency", f"{metrics.get('avg_latency_ms', 0)} ms")
    with m5:
        st.metric("P95 Latency", f"{metrics.get('p95_latency_ms', 0)} ms")

    st.divider()

    # Distributions
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.markdown("##### 📂 Cases by Complaint Category")
        cat_dist = metrics.get("category_distribution", {})
        if cat_dist:
            st.bar_chart(cat_dist)
        else:
            st.caption("No category data recorded.")

    with col_chart2:
        st.markdown("##### 🎯 Cases by Priority")
        prio_dist = metrics.get("priority_distribution", {})
        if prio_dist:
            st.bar_chart(prio_dist)
        else:
            st.caption("No priority data recorded.")

    st.divider()

    # Raw Log Inspection
    with st.expander("📜 Recent Operational Traces (logs/agent_ops.jsonl)", expanded=False):
        raw_logs = load_raw_logs()
        if raw_logs:
            st.caption(f"Showing last 15 of {len(raw_logs)} events.")
            recent_logs = raw_logs[-15:]
            for entry in reversed(recent_logs):
                ts = entry.get("timestamp", "")
                cid = entry.get("case_id", "UNKNOWN")
                etype = entry.get("event_type", "unknown")
                details = entry.get("details", {})
                st.markdown(f"`{ts}` | **{cid}** | `{etype}`: `{json.dumps(details)}`")
        else:
            st.info("No operational log entries found.")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 4: ML Fraud Model Diagnostics (Member 1)
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "🧠 ML Fraud Model":
    st.title("ML Fraud Detection Model")
    st.caption("Supervised ML classifier trained on Credit Card Fraud dataset.")

    metrics_file = ROOT / "ml" / "model_metrics.json"
    if not metrics_file.exists():
        st.warning("ml/model_metrics.json not found. Train the model using ml/train_model.py.")
    else:
        metrics_data = json.loads(metrics_file.read_text(encoding="utf-8"))

        selected = metrics_data.get("selected_model", "random_forest")
        rf_metrics = metrics_data.get("models", {}).get("random_forest", {})
        lr_metrics = metrics_data.get("models", {}).get("logistic_regression", {})

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        with col_m1:
            st.metric("Selected Model", selected.replace("_", " ").title())
        with col_m2:
            st.metric("PR-AUC", f"{rf_metrics.get('pr_auc', 0):.4f}")
        with col_m3:
            st.metric("Precision", f"{rf_metrics.get('precision', 0):.4f}")
        with col_m4:
            st.metric("Recall", f"{rf_metrics.get('recall', 0):.4f}")

        st.divider()

        st.markdown("##### 📊 Model Comparison: Random Forest vs. Logistic Regression")
        comp_data = {
            "Metric": ["PR-AUC", "ROC-AUC", "Precision", "Recall", "F1-Score"],
            "Random Forest (Selected)": [
                f"{rf_metrics.get('pr_auc', 0):.4f}",
                f"{rf_metrics.get('roc_auc', 0):.4f}",
                f"{rf_metrics.get('precision', 0):.4f}",
                f"{rf_metrics.get('recall', 0):.4f}",
                f"{rf_metrics.get('f1_score', 0):.4f}",
            ],
            "Logistic Regression": [
                f"{lr_metrics.get('pr_auc', 0):.4f}",
                f"{lr_metrics.get('roc_auc', 0):.4f}",
                f"{lr_metrics.get('precision', 0):.4f}",
                f"{lr_metrics.get('recall', 0):.4f}",
                f"{lr_metrics.get('f1_score', 0):.4f}",
            ],
        }
        st.table(comp_data)
