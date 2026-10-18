"""
app.py — Streamlit Case Management & Agent Ops Dashboard for Dispute Triage.

Member 3 owns this module.
Provides:
  1. Dispute Submission & AI Triage (Customer & Operator view)
  2. Case Management Review Queue
  3. Agent Ops Traces & System Metrics
  4. ML Fraud Model Diagnostics (Member 1 integration)

Run with:
    streamlit run app/app.py
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
    page_title="Card Dispute Triage Service",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ────────────────────────────────────────────────────────────────
st.markdown(
    """
    <style>
    .main-header { font-size: 2.2rem; font-weight: 700; color: #1E293B; margin-bottom: 0.2rem; }
    .sub-header { font-size: 1.05rem; color: #64748B; margin-bottom: 1.5rem; }
    .badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.03em;
    }
    .badge-high { background-color: #FEE2E2; color: #991B1B; }
    .badge-medium { background-color: #FEF3C7; color: #92400E; }
    .badge-low { background-color: #DCFCE7; color: #166534; }
    .badge-unavailable { background-color: #F1F5F9; color: #475569; }
    .badge-review { background-color: #EDE9FE; color: #5B21B6; }

    .triage-card {
        background-color: #FFFFFF;
        border: 1px solid #E2E8F0;
        border-radius: 12px;
        padding: 20px;
        margin-top: 15px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .metric-box {
        background: #F8FAFC;
        border: 1px solid #E2E8F0;
        border-radius: 8px;
        padding: 12px 16px;
        text-align: center;
    }
    .timeline-step {
        border-left: 2px solid #3B82F6;
        padding-left: 14px;
        margin-left: 6px;
        margin-bottom: 10px;
        font-size: 0.88rem;
    }
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

STATUS_BADGES = {
    "under_review": ("Under Review", "badge-review"),
    "escalated": ("Escalated", "badge-high"),
    "resolved": ("Resolved", "badge-low"),
    "new": ("New Case", "badge-unavailable"),
}

PRIORITY_BADGES = {
    "high": ("High Priority", "badge-high"),
    "medium": ("Medium Priority", "badge-medium"),
    "review_required": ("Review Required", "badge-review"),
    "low": ("Low Priority", "badge-low"),
}


def render_badge(text: str, badge_class: str) -> str:
    return f'<span class="badge {badge_class}">{text}</span>'


# ── Sidebar Navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.image("https://img.icons8.com/fluency/96/bank-building.png", width=64)
    st.title("Dispute Triage")
    st.caption("AI-Powered Card Complaint Resolution")
    st.divider()

    selected_view = st.radio(
        "Navigation",
        [
            "📝 Submit & Triage Complaint",
            "📋 Case Management Queue",
            "📊 Agent Ops & Observability",
            "🧠 ML Fraud Model (Member 1)",
        ],
        index=0,
    )

    st.divider()
    st.markdown("### Architecture")
    st.caption(
        "• **Member 1**: Random Forest Fraud Model\n"
        "• **Member 2**: Gemini AI Agent & Tool Caller\n"
        "• **Member 3**: Integration, Dashboard & Agent Ops"
    )


# ════════════════════════════════════════════════════════════════════════════
# VIEW 1: Submit & Triage Complaint
# ════════════════════════════════════════════════════════════════════════════
if selected_view == "📝 Submit & Triage Complaint":
    st.markdown('<div class="main-header">Card Dispute Triage Service</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Submit customer dispute complaints to trigger automated AI classification, ML risk scoring, duplicate detection, and case prioritization.</div>',
        unsafe_allow_html=True,
    )

    # Demo scenario shortcuts
    st.markdown("##### ⚡ Quick Demonstration Scenarios")
    c1, c2, c3, c4 = st.columns(4)

    preset_complaint = ""
    preset_tx = "TX1001"

    with c1:
        if st.button("🚨 Unauthorized ₹20,000", use_container_width=True):
            st.session_state["complaint_input"] = (
                "I did not make this ₹20,000 payment to an online merchant at 2:15 AM. Please investigate immediately."
            )
            st.session_state["tx_input"] = "TX1001"
    with c2:
        if st.button("🔁 Duplicate Charge ₹1,200", use_container_width=True):
            st.session_state["complaint_input"] = (
                "I was charged twice for the same purchase at Example Restaurant. Both charges appeared at almost the same time."
            )
            st.session_state["tx_input"] = "TX1002"
    with c3:
        if st.button("📦 Goods Not Received", use_container_width=True):
            st.session_state["complaint_input"] = (
                "I paid for an order last week, but the items were never delivered by the merchant."
            )
            st.session_state["tx_input"] = "TX1002"
    with c4:
        if st.button("❓ Missing Transaction ID", use_container_width=True):
            st.session_state["complaint_input"] = (
                "I see an unauthorized charge on my card statement that I did not authorize."
            )
            st.session_state["tx_input"] = "TX-NOT-FOUND"

    col_form, col_history = st.columns([1.8, 1.2])

    with col_form:
        with st.form("triage_form"):
            default_text = st.session_state.get(
                "complaint_input",
                "I did not authorize this ₹20,000 transaction to Example Online Store at 2:15 AM.",
            )
            default_tx = st.session_state.get("tx_input", "TX1001")

            complaint_text = st.text_area(
                "Customer Complaint Text",
                value=default_text,
                height=120,
                help="Natural language dispute submitted by the cardholder.",
            )

            tx_col, btn_col = st.columns([1.5, 1])
            with tx_col:
                transaction_id = st.text_input(
                    "Transaction ID",
                    value=default_tx,
                    help="Transaction identifier from statement (e.g., TX1001, TX1002).",
                )
            with btn_col:
                st.write("")
                st.write("")
                submitted = st.form_submit_button(
                    "🔍 Run AI Triage",
                    type="primary",
                    use_container_width=True,
                )

        if submitted and complaint_text.strip():
            with st.spinner("AI Agent analyzing complaint, checking tools, and computing triage decision..."):
                with AgentTrace(complaint_text.strip(), transaction_id.strip()) as trace:
                    result = process_complaint(complaint_text.strip(), transaction_id.strip())
                    trace.set_result(result)

            st.session_state["latest_result"] = result
            st.session_state["latest_latency"] = trace.duration_ms

    # Display Triage Card if available
    latest_result = st.session_state.get("latest_result")
    latency_val = st.session_state.get("latest_latency", 0.0)

    if latest_result:
        with col_form:
            st.markdown("---")
            st.markdown("### 📋 Triage Decision Result")

            cat = latest_result.get("complaint_category", "unknown")
            cat_display = CATEGORY_NAMES.get(cat, cat.replace("_", " ").title())
            prio = latest_result.get("priority", "review_required")
            prio_text, prio_cls = PRIORITY_BADGES.get(prio, (prio, "badge-review"))
            status = latest_result.get("status", "under_review")
            status_text, status_cls = STATUS_BADGES.get(status, (status, "badge-review"))
            risk = latest_result.get("risk_level", "unavailable")
            risk_cls = f"badge-{risk.lower()}" if risk.lower() in ("high", "medium", "low") else "badge-unavailable"

            # Top KPI Cards
            k1, k2, k3, k4 = st.columns(4)
            with k1:
                st.markdown(
                    f'<div class="metric-box"><small>Case ID</small><br><b>{latest_result.get("case_id")}</b></div>',
                    unsafe_allow_html=True,
                )
            with k2:
                st.markdown(
                    f'<div class="metric-box"><small>Priority</small><br>{render_badge(prio_text, prio_cls)}</div>',
                    unsafe_allow_html=True,
                )
            with k3:
                st.markdown(
                    f'<div class="metric-box"><small>Risk Level</small><br>{render_badge(risk.upper(), risk_cls)}</div>',
                    unsafe_allow_html=True,
                )
            with k4:
                st.markdown(
                    f'<div class="metric-box"><small>Case Status</small><br>{render_badge(status_text, status_cls)}</div>',
                    unsafe_allow_html=True,
                )

            st.markdown("")

            # Action & Evidence
            col_act, col_ev = st.columns([1, 1])
            with col_act:
                st.markdown("##### 📌 Recommended Action")
                st.info(latest_result.get("recommended_action", "No action specified."))

                requires_hr = latest_result.get("requires_human_review", True)
                if requires_hr:
                    st.warning("⚠️ **Human Review Required**: Case routed to fraud investigator queue.")
                else:
                    st.success("✅ **Automated Resolution Eligible**")

                if latest_result.get("error"):
                    st.error(f"**Notice**: {latest_result['error']}")

            with col_ev:
                st.markdown("##### 📑 Evidence Gathered")
                evidence_list = latest_result.get("evidence_summary", [])
                if evidence_list:
                    for ev in evidence_list:
                        st.markdown(f"- {ev}")
                else:
                    st.caption("No evidence items available (e.g. transaction lookup failed).")

                prob = latest_result.get("fraud_probability")
                if prob is not None:
                    st.metric("Fraud Model Probability", f"{prob:.1%}")
                else:
                    st.caption("Fraud Probability: *N/A (model features not present or not requested)*")

    with col_history:
        st.markdown("### 🛰️ Live Agent Ops Trace")
        if latest_result:
            case_id = latest_result.get("case_id")
            traces = get_case_traces()
            case_events = traces.get(case_id, [])

            st.caption(f"Execution Latency: **{latency_val} ms** | Events Logged: **{len(case_events)}**")

            if case_events:
                for idx, ev in enumerate(case_events):
                    etype = ev.get("event_type", "unknown")
                    ts = ev.get("timestamp", "")[11:19]
                    details = ev.get("details", {})
                    st.markdown(
                        f"""
                        <div class="timeline-step">
                            <b>Step {idx + 1}: {etype.replace('_', ' ').title()}</b> <small style="color:#64748B;">({ts})</small><br>
                            <code>{json.dumps(details)}</code>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
            else:
                st.info("Event trace recorded in `logs/agent_ops.jsonl`.")
        else:
            st.info("Submit a complaint or choose a quick scenario above to watch the agent execution trace unfold live.")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 2: Case Management Queue
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "📋 Case Management Queue":
    st.markdown('<div class="main-header">Case Management Queue</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">All complaints triaged by the AI Agent and persisted in data/cases.json.</div>',
        unsafe_allow_html=True,
    )

    cases = load_cases()

    if not cases:
        st.info("No cases currently in the database. Submit a complaint to create the first case.")
    else:
        # Filter controls
        f1, f2, f3, f4 = st.columns(4)
        with f1:
            all_statuses = ["All"] + sorted({c.get("status", "unknown") for c in cases})
            sel_status = st.selectbox("Status", all_statuses)
        with f2:
            all_categories = ["All"] + sorted({c.get("complaint_category", "unknown") for c in cases})
            sel_cat = st.selectbox("Category", all_categories)
        with f3:
            all_priorities = ["All"] + sorted({c.get("priority", "unknown") for c in cases})
            sel_prio = st.selectbox("Priority", all_priorities)
        with f4:
            all_risks = ["All"] + sorted({c.get("risk_level", "unavailable") for c in cases})
            sel_risk = st.selectbox("Risk Level", all_risks)

        # Apply filters
        filtered_cases = [
            c for c in cases
            if (sel_status == "All" or c.get("status") == sel_status)
            and (sel_cat == "All" or c.get("complaint_category") == sel_cat)
            and (sel_prio == "All" or c.get("priority") == sel_prio)
            and (sel_risk == "All" or c.get("risk_level", "unavailable") == sel_risk)
        ]

        st.caption(f"Showing **{len(filtered_cases)}** of **{len(cases)}** total cases.")

        for c in reversed(filtered_cases):
            cid = c.get("case_id", "UNKNOWN")
            txid = c.get("transaction_id", "N/A")
            cat = c.get("complaint_category", "unknown")
            cat_label = CATEGORY_NAMES.get(cat, cat)
            prio = c.get("priority", "review_required")
            status = c.get("status", "under_review")

            with st.expander(f"📁 {cid} | TX: {txid} | {cat_label} [{prio.upper()}]"):
                c_col1, c_col2 = st.columns([1.2, 1])
                with c_col1:
                    st.markdown(f"**Category:** `{cat}`")
                    st.markdown(f"**Priority:** `{prio}`")
                    st.markdown(f"**Status:** `{status}`")
                    st.markdown(f"**Recommended Action:**")
                    st.info(c.get("recommended_action", "None"))
                with c_col2:
                    st.markdown(f"**Risk Level:** `{c.get('risk_level', 'unavailable')}`")
                    st.markdown(f"**Fraud Probability:** `{c.get('fraud_probability')}`")
                    st.markdown(f"**Requires Human Review:** `{c.get('requires_human_review')}`")
                    if c.get("error"):
                        st.error(f"Error: {c['error']}")

                st.markdown("**Evidence Summary:**")
                ev_items = c.get("evidence_summary", [])
                if ev_items:
                    for ev in ev_items:
                        st.markdown(f"- {ev}")
                else:
                    st.caption("No evidence items.")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 3: Agent Ops & Observability
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "📊 Agent Ops & Observability":
    st.markdown('<div class="main-header">Agent Ops & Observability</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">System metrics, event logs, and operational telemetry from logs/agent_ops.jsonl.</div>',
        unsafe_allow_html=True,
    )

    metrics = compute_agent_ops_metrics()

    # KPI Row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Total Cases", metrics["total_cases"])
    with m2:
        st.metric("Total Events", metrics["total_events"])
    with m3:
        st.metric("Success Rate", f"{metrics['success_rate']}%")
    with m4:
        st.metric("Avg Latency", f"{metrics['avg_latency_ms']} ms")
    with m5:
        st.metric("P95 Latency", f"{metrics['p95_latency_ms']} ms")

    st.divider()

    # Distributions
    col_chart1, col_chart2 = st.columns(2)

    with col_chart1:
        st.markdown("##### 📂 Cases by Complaint Category")
        cat_dist = metrics.get("category_distribution", {})
        if cat_dist:
            st.bar_chart(cat_dist)
        else:
            st.caption("No category data available.")

        st.markdown("##### ⚡ Classifier Method Distribution")
        clf_data = {
            "Gemini AI (Structured)": metrics.get("gemini_classification_count", 0),
            "Keyword Fallback": metrics.get("fallback_classification_count", 0),
        }
        st.bar_chart(clf_data)

    with col_chart2:
        st.markdown("##### 🎯 Cases by Priority")
        prio_dist = metrics.get("priority_distribution", {})
        if prio_dist:
            st.bar_chart(prio_dist)
        else:
            st.caption("No priority data available.")

        st.markdown("##### 🚦 Operational Events by Type")
        ev_dist = metrics.get("event_distribution", {})
        if ev_dist:
            st.bar_chart(ev_dist)
        else:
            st.caption("No event logs recorded.")

    st.divider()

    # Raw Log Inspection
    st.markdown("##### 📜 Recent Operational Traces (logs/agent_ops.jsonl)")
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
elif selected_view == "🧠 ML Fraud Model (Member 1)":
    st.markdown('<div class="main-header">ML Fraud Detection Model</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="sub-header">Supervised ML classifier trained on the Credit Card Fraud dataset (Member 1).</div>',
        unsafe_allow_html=True,
    )

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
            st.metric("PR-AUC (Primary Metric)", f"{rf_metrics.get('pr_auc', 0):.4f}")
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

        col_cm, col_feats = st.columns([1, 1])

        with col_cm:
            st.markdown("##### 🧮 Confusion Matrix (Random Forest)")
            cm = rf_metrics.get("confusion_matrix", [[0, 0], [0, 0]])
            st.write(
                f"- **True Negatives (Legitimate detected)**: {cm[0][0]:,}\n"
                f"- **False Positives (False alarms)**: {cm[0][1]:,}\n"
                f"- **False Negatives (Missed fraud)**: {cm[1][0]:,}\n"
                f"- **True Positives (Fraud caught)**: {cm[1][1]:,}"
            )

        with col_feats:
            st.markdown("##### 📐 Input Feature Vector")
            feats = metrics_data.get("feature_names", [])
            st.caption(f"Requires exactly {len(feats)} input features:")
            st.code(", ".join(feats), language="text")
