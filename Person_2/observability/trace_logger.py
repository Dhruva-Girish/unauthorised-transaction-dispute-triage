"""
trace_logger.py — AgentOps Tool-Call Logging & Execution Tracing (Unit 4.F)
Records tool execution parameters, latencies, node transitions, and failure states.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TRACE_LOG_FILE = ROOT.parent / "Person_3" / "logs" / "agent_ops.jsonl"


class AgentOpsTraceLogger:
    """Detailed tool execution and agent workflow logger."""

    def __init__(self, log_path: Path | str | None = None) -> None:
        self.log_path = Path(log_path) if log_path else TRACE_LOG_FILE
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def log_event(
        self,
        case_id: str,
        event_type: str,
        details: dict[str, Any] | None = None,
        duration_ms: float | None = None,
    ) -> dict[str, Any]:
        """Record an operational trace event."""
        payload = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "event_type": event_type,
            "duration_ms": duration_ms,
            "details": details or {},
        }
        try:
            with self.log_path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(payload, ensure_ascii=False) + "\n")
        except OSError:
            pass
        return payload

    def log_tool_call(
        self,
        case_id: str,
        tool_name: str,
        input_args: dict[str, Any],
        output_result: Any,
        duration_ms: float,
        success: bool = True,
    ) -> None:
        """Record specific tool execution details."""
        self.log_event(
            case_id=case_id,
            event_type="tool_execution",
            duration_ms=duration_ms,
            details={
                "tool_name": tool_name,
                "input": input_args,
                "output_preview": str(output_result)[:150],
                "success": success,
            },
        )


# Global trace logger
agent_logger = AgentOpsTraceLogger()
