"""
orchestrator.py — High-Level Agent Orchestrator (Unit 4.A & 4.B)
Routes dispute tasks between primary LangGraph workflow and CrewAI multi-agent investigation.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .triage_agent import process_complaint
from crewai.fraud_crew import fraud_crew


class AgentOrchestrator:
    """Master orchestrator for single-agent and multi-agent dispute resolution."""

    @staticmethod
    def triage(complaint_text: str, transaction_id: str, mode: str = "langgraph") -> dict[str, Any]:
        """
        Execute triage under selected orchestration mode:
          - 'langgraph': Structured stateful DAG workflow (default)
          - 'crewai': Specialized 3-agent investigation crew (Investigator, Compliance, Risk Auditor)
        """
        if mode.lower() == "crewai":
            return fraud_crew.run_investigation(complaint_text, transaction_id)
        return process_complaint(complaint_text, transaction_id)


agent_orchestrator = AgentOrchestrator()
