
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

LOG_FILE = (
    Path(__file__).resolve().parent.parent
    / "logs"
    / "agent_ops.jsonl"
)


def log_event(
    case_id: str,
    event_type: str,
    details: dict[str, Any] | None = None,
) -> None:
    """Append one structured operational event to a JSONL file."""
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "case_id": case_id,
        "event_type": event_type,
        "details": details or {},
    }

    try:
        LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

        with LOG_FILE.open("a", encoding="utf-8") as file:
            file.write(json.dumps(event) + "\n")
    except OSError:
        # Logging failures must not stop complaint processing.
        pass
