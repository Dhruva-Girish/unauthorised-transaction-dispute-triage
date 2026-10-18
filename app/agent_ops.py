"""
agent_ops.py — Agent Ops monitoring, trace recording, and metrics analysis for Member 3.

Reads logs from logs/agent_ops.jsonl and cases from data/cases.json.
Provides execution tracing, timing, event log parsing, and performance metrics.
"""

from __future__ import annotations

import json
import time
from datetime import datetime
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOG_FILE = ROOT / "logs" / "agent_ops.jsonl"
CASES_FILE = ROOT / "data" / "cases.json"


def load_raw_logs() -> list[dict[str, Any]]:
    """Return all raw operational events from logs/agent_ops.jsonl."""
    if not LOG_FILE.exists():
        return []
    events = []
    for line in LOG_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                events.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return events


def get_case_traces() -> dict[str, list[dict[str, Any]]]:
    """Group event logs by case_id to form chronological execution traces."""
    traces: dict[str, list[dict[str, Any]]] = {}
    for event in load_raw_logs():
        case_id = event.get("case_id", "UNKNOWN")
        if case_id not in traces:
            traces[case_id] = []
        traces[case_id].append(event)
    return traces


def compute_agent_ops_metrics() -> dict[str, Any]:
    """
    Compute aggregate Agent Ops performance and distribution metrics.
    Analyzes event logs and persisted case records.
    """
    from agent.case_store import load_cases

    cases = load_cases()
    raw_logs = load_raw_logs()
    traces = get_case_traces()

    total_cases = len(cases)
    total_events = len(raw_logs)

    # Categories and Priorities
    category_counts: dict[str, int] = {}
    priority_counts: dict[str, int] = {}
    risk_counts: dict[str, int] = {}
    status_counts: dict[str, int] = {}

    for case in cases:
        cat = case.get("complaint_category", "unknown")
        prio = case.get("priority", "unknown")
        risk = case.get("risk_level", "unavailable")
        stat = case.get("status", "unknown")

        category_counts[cat] = category_counts.get(cat, 0) + 1
        priority_counts[prio] = priority_counts.get(prio, 0) + 1
        risk_counts[risk] = risk_counts.get(risk, 0) + 1
        status_counts[stat] = status_counts.get(stat, 0) + 1

    # Event types distribution
    event_counts: dict[str, int] = {}
    fallback_count = 0
    gemini_count = 0
    error_count = 0

    for event in raw_logs:
        etype = event.get("event_type", "unknown")
        event_counts[etype] = event_counts.get(etype, 0) + 1

        if etype == "classification_completed":
            gemini_count += 1
        elif etype == "classification_fallback":
            fallback_count += 1
        elif etype in ("processing_error", "case_storage_error"):
            error_count += 1

    # Latency calculation per trace
    latencies_ms: list[float] = []
    for case_id, events in traces.items():
        if len(events) >= 2:
            try:
                t0 = datetime.fromisoformat(events[0]["timestamp"])
                t1 = datetime.fromisoformat(events[-1]["timestamp"])
                diff_ms = max(0.0, (t1 - t0).total_seconds() * 1000.0)
                latencies_ms.append(diff_ms)
            except Exception:
                pass

    avg_latency = round(sum(latencies_ms) / len(latencies_ms), 1) if latencies_ms else 0.0
    latencies_ms.sort()
    p95_latency = (
        round(latencies_ms[int(len(latencies_ms) * 0.95)], 1)
        if latencies_ms
        else 0.0
    )

    success_rate = (
        round(((total_cases - error_count) / total_cases) * 100.0, 1)
        if total_cases > 0
        else 100.0
    )

    return {
        "total_cases": total_cases,
        "total_events": total_events,
        "success_rate": success_rate,
        "error_count": error_count,
        "gemini_classification_count": gemini_count,
        "fallback_classification_count": fallback_count,
        "avg_latency_ms": avg_latency,
        "p95_latency_ms": p95_latency,
        "category_distribution": category_counts,
        "priority_distribution": priority_counts,
        "risk_distribution": risk_counts,
        "status_distribution": status_counts,
        "event_distribution": event_counts,
    }


class AgentTrace:
    """
    Context manager to time execution and capture structured trace metadata.
    """

    def __init__(self, complaint_text: str, transaction_id: str) -> None:
        self.complaint_text = complaint_text
        self.transaction_id = transaction_id
        self._start_time: float = 0.0
        self.duration_ms: float = 0.0
        self.result: dict[str, Any] | None = None
        self.error: str | None = None

    def __enter__(self) -> "AgentTrace":
        self._start_time = time.perf_counter()
        return self

    def set_result(self, result: dict[str, Any]) -> None:
        self.result = result

    def set_error(self, error: str) -> None:
        self.error = error

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        self.duration_ms = round((time.perf_counter() - self._start_time) * 1000.0, 2)
        if exc_val and not self.error:
            self.error = str(exc_val)
        return False
