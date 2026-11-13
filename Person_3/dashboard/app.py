"""
app.py — Streamlit Case Management & Dispute Triage Dashboard (Person 3)
Clean, modern, uncluttered UI supporting both Light and Dark themes natively.
"""

from __future__ import annotations

import json
import sys
import time
from pathlib import Path
from typing import Any

import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from Person_2.agents.triage_agent import process_complaint
from database.case_repository import case_repo
from monitoring.sla_monitor import sla_monitor
from Person_1.models.registry import get_model_metadata, load_metrics
from Person_1.feature_store.feature_pipeline import feast_store
from Person_1.monitoring.drift_monitor import DataDriftMonitor

# ── Page Configuration ─────────────────────────────────────────────────────
st.set_page_config(
    page_title="Card Dispute Triage",
    page_icon="💳",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme-Safe Custom CSS (No hardcoded light backgrounds) ─────────────────
st.markdown(
    """
    <style>
    /* Clean, responsive spacing */
    .block-container { padding-top: 2rem; padding-bottom: 2rem; max-width: 1200px; }
    h1, h2, h3 { margin-bottom: 0.5rem; }
    .stAlert { margin-top: 0.5rem; margin-bottom: 0.5rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

CATEGORY_NAMES = {
    "unauthorized_transaction": "Unauthorized Transaction",
    "duplicate_payment": "Duplicate Payment",
    "goods_not_received": "Goods Not Received",
    "billing_dispute": "Billing Dispute",
    "other": "Other",
    "unknown": "Unclassified",
}

PRESETS = {
    "-- Type or paste custom complaint --": {
        "text": "",
        "tx": "TX1001",
    },
    "🚨 Unauthorized ₹20,000 at 2:15 AM": {
        "text": "I did not make this ₹20,000 transaction to an online store at 2:15 AM. My card was with me. Please investigate immediately.",
        "tx": "TX1001",
    },
    "🔁 Duplicate Restaurant Billing ₹1,200": {
        "text": "I was charged twice for the same dinner at Example Restaurant. Both charges appeared within 3 minutes of each other.",
        "tx": "TX1002",
    },
    "📦 Goods Never Received": {
        "text": "I ordered headphones online 3 weeks ago, paid in full, but the merchant never delivered them and the tracking link is dead.",
        "tx": "TX1002",
    },
    "❌ Cancelled Gym Subscription Billed Again": {
        "text": "I cancelled my gym membership last month and confirmed cancellation with staff, but they billed my card again this morning.",
        "tx": "TX1001",
    },
    "❓ Unknown Charge (No Transaction ID)": {
        "text": "Someone charged my card while I was asleep yesterday, I don't know the exact transaction reference code.",
        "tx": "TX-NOT-FOUND",
    },
}

# ── Sidebar Navigation ──────────────────────────────────────────────────────
with st.sidebar:
    st.title("💳 Dispute Triage")
    st.caption("AI-Powered Card Dispute Risk & Triage Platform")
    st.divider()

    selected_view = st.radio(
        "Navigation",
        [
            "📝 Triage Dispute",
            "📋 Investigation Queue",
            "⚙️ System & Model Metrics",
        ],
        index=0,
    )

    st.divider()
    st.caption("**Safety Guarantee**: Unauthorized claims are never auto-dismissed based on ML scores alone.")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 1: Triage Dispute (Simple, Focused, Minimalist)
# ════════════════════════════════════════════════════════════════════════════
if selected_view == "📝 Triage Dispute":
    st.title("Card Dispute Triage")
    st.caption("Submit customer complaints to instantly classify category, detect duplicates, score fraud risk, and assign investigation priority.")

    with st.container(border=True):
        # Preset selector
        selected_preset = st.selectbox(
            "Quick Scenario Presets (Optional)",
            list(PRESETS.keys()),
            index=0,
        )

        preset_data = PRESETS[selected_preset]

        with st.form("triage_submission_form", clear_on_submit=False):
            col_tx, col_btn = st.columns([1, 2])
            with col_tx:
                tx_val = preset_data["tx"] if preset_data["tx"] else "TX1001"
                tx_id = st.text_input("Transaction ID", value=tx_val, help="Identifier of the disputed transaction")

            complaint_val = preset_data["text"] if preset_data["text"] else "I did not authorize this charge of ₹20,000 on my card statement."
            complaint_text = st.text_area("Customer Complaint", value=complaint_val, height=100)

            submitted = st.form_submit_button("🔍 Run Triage Analysis", type="primary", use_container_width=True)

    if submitted and complaint_text.strip():
        with st.spinner("Analyzing complaint and calculating risk..."):
            t0 = time.perf_counter()
            result = process_complaint(complaint_text.strip(), tx_id.strip())
            dur_ms = round((time.perf_counter() - t0) * 1000.0, 2)
            case_repo.save_case(result)
            sla_monitor.record_request(dur_ms, is_success=True)

            st.session_state["latest_result"] = result
            st.session_state["latest_latency"] = dur_ms

    latest_result = st.session_state.get("latest_result")

    if latest_result:
        st.subheader("📋 Triage Recommendation")

        cat_raw = latest_result.get("complaint_category", "unknown")
        cat_label = CATEGORY_NAMES.get(cat_raw, cat_raw.replace("_", " ").title())
        priority = (latest_result.get("priority") or "review_required").upper()
        prob = latest_result.get("fraud_probability")
        prob_str = f"{prob:.1%}" if prob is not None else "N/A"
        risk_level = (latest_result.get("risk_level") or "Unavailable").capitalize()
        requires_hr = latest_result.get("requires_human_review", True)
        case_id = latest_result.get("case_id", "N/A")

        # 4-card result summary — use markdown labels + metric values for dark-mode safety
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown("**Dispute Category**")
            st.markdown(f"### {cat_label}")
        with m2:
            st.metric("Priority Queue", priority)
        with m3:
            st.metric("ML Fraud Risk", prob_str, delta=risk_level, delta_color="off")
        with m4:
            st.metric("Human Review", "Required" if requires_hr else "Auto-Resolved")

        # Action banner
        rec_action = latest_result.get("recommended_action", "Review claim manually.")
        if requires_hr:
            st.warning(f"**Recommended Action:** {rec_action}")
        else:
            st.success(f"**Recommended Action:** {rec_action}")

        # Clean evidence display
        evidence = latest_result.get("evidence_summary", [])
        if evidence:
            with st.container(border=True):
                st.markdown("**Evidence & Findings:**")
                for item in evidence:
                    # Clean up policy citations so they look like neat quotes
                    if "Policy Reference:" in item:
                        st.caption(f"📜 {item}")
                    else:
                        st.markdown(f"• {item}")

        # Collapsible technical details for developers/auditors (Keeps UI uncluttered)
        with st.expander("🔍 Technical Audit & Agent Trace", expanded=False):
            t_col1, t_col2 = st.columns(2)
            with t_col1:
                st.markdown(f"**Case Reference:** `{case_id}`")
                st.markdown(f"**Transaction ID:** `{latest_result.get('transaction_id')}`")
                st.markdown(f"**Execution Latency:** `{st.session_state.get('latest_latency', 0)} ms`")
            with t_col2:
                meta = latest_result.get("execution_metadata", {})
                steps = meta.get("steps", ["classify_complaint", "lookup_transaction", "synthesize_decision"])
                st.markdown(f"**Workflow Steps ({len(steps)}):** " + " ➔ ".join([f"`{s}`" for s in steps]))

            st.json(latest_result)


# ════════════════════════════════════════════════════════════════════════════
# VIEW 2: Case Management Queue
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "📋 Investigation Queue":
    st.title("Case Management Queue")
    st.caption("Active dispute cases saved in SQLite database.")

    cases = case_repo.list_cases(limit=100)

    if not cases:
        st.info("No cases currently in the database. Submit a complaint to create the first case.")
    else:
        # Simple search and filter
        f1, f2, f3 = st.columns([1, 1, 1])
        with f1:
            all_statuses = ["All"] + sorted({c.get("status", "unknown") for c in cases})
            sel_status = st.selectbox("Filter Status", all_statuses)
        with f2:
            all_categories = ["All"] + sorted({c.get("complaint_category", "unknown") for c in cases})
            sel_cat = st.selectbox("Filter Category", all_categories)
        with f3:
            all_priorities = ["All"] + sorted({c.get("priority", "unknown") for c in cases})
            sel_prio = st.selectbox("Filter Priority", all_priorities)

        filtered = [
            c for c in cases
            if (sel_status == "All" or c.get("status") == sel_status)
            and (sel_cat == "All" or c.get("complaint_category") == sel_cat)
            and (sel_prio == "All" or c.get("priority") == sel_prio)
        ]

        st.caption(f"Showing **{len(filtered)}** case(s).")

        for c in filtered:
            cid = c.get("case_id", "UNKNOWN")
            txid = c.get("transaction_id", "N/A")
            cat = c.get("complaint_category", "unknown")
            cat_label = CATEGORY_NAMES.get(cat, cat)
            prio = (c.get("priority") or "review_required").upper()
            status = c.get("status", "under_review").upper()

            with st.expander(f"📁 **{cid}** — {cat_label} | TX: {txid} | **[{prio}]** Status: {status}"):
                c1, c2 = st.columns([1.5, 1])
                with c1:
                    st.markdown(f"**Recommended Action:**")
                    st.info(c.get("recommended_action", "Review claim."))
                    ev_items = c.get("evidence_summary", [])
                    if ev_items:
                        st.markdown("**Evidence:**")
                        for ev in ev_items:
                            st.markdown(f"• {ev}")
                with c2:
                    st.metric("Fraud Score", f"{c.get('fraud_probability'):.1%}" if c.get('fraud_probability') is not None else "N/A")
                    st.metric("Risk Level", (c.get('risk_level') or "Unavailable").capitalize())
                    st.caption(f"Requires Human Review: **{c.get('requires_human_review')}**")


# ════════════════════════════════════════════════════════════════════════════
# VIEW 3: System & Model Metrics (SLA, Feast, Drift)
# ════════════════════════════════════════════════════════════════════════════
elif selected_view == "⚙️ System & Model Metrics":
    st.title("System Observability & Model Performance")
    st.caption("SLA compliance, latency percentiles, Feast Feature Store, and Data Drift diagnostics.")

    sla_stats = sla_monitor.get_compliance_metrics()
    cases = case_repo.list_cases(limit=200)

    # Key Performance Metrics
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.metric("Total Cases Triaged", len(cases))
    with k2:
        st.metric("P50 Latency", f"{sla_stats.get('p50_latency_ms', 0)} ms")
    with k3:
        st.metric("P95 Latency", f"{sla_stats.get('p95_latency_ms', 0)} ms")
    with k4:
        st.metric("SLA Latency Target", "< 500 ms")

    st.divider()

    tab_model, tab_feast, tab_drift = st.tabs(["🧠 ML Model", "🍽️ Feast Feature Store", "📉 Data Drift"])

    with tab_model:
        meta = get_model_metadata()
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.metric("Production Model", meta.get("model_name", "Random Forest").replace("_", " ").title())
        with m_col2:
            st.metric("Selection Metric", meta.get("selection_metric", "PR-AUC"))
        with m_col3:
            st.metric("Decision Threshold", meta.get("selected_threshold", 0.5))

    with tab_feast:
        st.markdown("##### Feast Online Feature Lookup")
        test_tx = st.text_input("Entity Key (transaction_id)", value="TX1000")
        if st.button("Fetch Live Feast Features"):
            res = feast_store.get_online_features([{"transaction_id": test_tx}])
            if res and "error" not in res[0]:
                st.success(f"Features retrieved for {test_tx} in < 2ms:")
                st.json(res[0])
            else:
                st.warning(f"Entity '{test_tx}' not found in online store.")

    with tab_drift:
        st.markdown("##### Ingestion Data Drift Monitor (KS-Test & PSI)")
        if st.button("Run Drift Check on Reference Baseline"):
            monitor = DataDriftMonitor()
            if not monitor.baseline_df.empty:
                drift_rep = monitor.check_drift(monitor.baseline_df.sample(200, random_state=42))
                st.write(f"**Drift Detected:** `{drift_rep['has_drift']}`")
                st.info(drift_rep["recommendation"])
            else:
                st.warning("Baseline reference dataset not found.")
