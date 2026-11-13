"""
events.py — Structured Audit Events and Logging Contracts
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any
from .enums import EventType


class AuditEvent:
    """Standardized operational event envelope."""

    def __init__(
        self,
        case_id: str,
        event_type: EventType | str,
        details: dict[str, Any] | None = None,
        source_service: str = "dispute-service",
        timestamp: str | None = None,
    ) -> None:
        self.case_id = case_id
        self.event_type = (
            event_type.value if isinstance(event_type, EventType) else str(event_type)
        )
        self.details = details or {}
        self.source_service = source_service
        self.timestamp = timestamp or datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "case_id": self.case_id,
            "event_type": self.event_type,
            "source_service": self.source_service,
            "details": self.details,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)
