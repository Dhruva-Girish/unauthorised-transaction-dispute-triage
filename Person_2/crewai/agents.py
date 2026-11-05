"""
agents.py — Autonomous CrewAI Agent Definitions (Unit 4.A)
Defines specialized multi-agent roles: Investigator, Compliance Officer, and Risk Auditor.
"""

from __future__ import annotations

from typing import Any

try:
    from crewai import Agent
    CREWAI_AVAILABLE = True
except ImportError:
    CREWAI_AVAILABLE = False


def create_dispute_investigator_agent() -> Any:
    """Dispute Investigator: Analyzes claim details, timeline, and customer transaction habits."""
    role = "Senior Dispute Investigator"
    goal = "Investigate the veracity of the customer's transaction dispute and detect billing anomalies."
    backstory = (
        "An experienced bank card dispute investigator with 15 years evaluating cardholder "
        "statements, merchant dispute evidence, and duplicate billing occurrences."
    )
    if CREWAI_AVAILABLE:
        return Agent(role=role, goal=goal, backstory=backstory, verbose=False, memory=True)
    return {"role": role, "goal": goal, "backstory": backstory}


def create_policy_compliance_agent() -> Any:
    """Policy Compliance Officer: Validates chargeback rights, notice deadlines, and Regulation E."""
    role = "Card Dispute Policy Compliance Officer"
    goal = "Ensure dispute recommendations strictly adhere to banking regulations and anti-dismissal rules."
    backstory = (
        "A banking compliance attorney specialized in Electronic Fund Transfer Act / Regulation E rules, "
        "ensuring customer dispute rights are preserved and low ML scores never improperly dismiss claims."
    )
    if CREWAI_AVAILABLE:
        return Agent(role=role, goal=goal, backstory=backstory, verbose=False, memory=True)
    return {"role": role, "goal": goal, "backstory": backstory}


def create_risk_auditor_agent() -> Any:
    """Risk Auditor: Evaluates machine learning fraud scoring, device anomalies, and priority queue."""
    role = "Fraud Risk & Systems Auditor"
    goal = "Synthesize ML fraud probabilities with transaction features to assign appropriate case priority."
    backstory = (
        "An expert quantitative risk auditor who cross-references supervised ML risk scores "
        "with historical fraud rates to assign optimized investigator queues."
    )
    if CREWAI_AVAILABLE:
        return Agent(role=role, goal=goal, backstory=backstory, verbose=False, memory=True)
    return {"role": role, "goal": goal, "backstory": backstory}
