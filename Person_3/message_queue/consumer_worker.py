"""
consumer_worker.py — Background Message Queue Consumer Worker (Unit 1.B & 1.C)
Consumes dispute submissions asynchronously, executes AI triage, persists cases, and dispatches webhooks.
"""

from __future__ import annotations

import sys
import threading
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PROJECT_ROOT = ROOT.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from .queue_broker import message_broker
from database.case_repository import case_repo
from webhooks.dispatcher import webhook_dispatcher


class ConsumerWorker:
    """Background consumer daemon processing queued disputes."""

    def __init__(self, broker=None, auto_start: bool = False) -> None:
        self.broker = broker or message_broker
        self.running = False
        self._thread: threading.Thread | None = None
        self.processed_count = 0
        if auto_start:
            self.start()

    def start(self) -> None:
        """Start consumer background thread."""
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._run_loop, daemon=True)
            self._thread.start()

    def stop(self) -> None:
        """Stop consumer loop gracefully."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=2.0)

    def _run_loop(self) -> None:
        while self.running:
            msg = self.broker.consume(block=True, timeout=1.0)
            if msg:
                self._process_message(msg)

    def _process_message(self, message: dict[str, Any]) -> dict[str, Any]:
        """Triage the queued complaint, save result, and emit webhooks."""
        payload = message.get("payload", {})
        complaint = payload.get("complaint_text", "")
        tx_id = payload.get("transaction_id", "")

        try:
            from Person_2.agents.triage_agent import process_complaint
            result = process_complaint(complaint, tx_id)
            case_repo.save_case(result)

            # Webhook notifications on high-priority / fraud events
            if result.get("priority") == "high":
                webhook_dispatcher.dispatch_event("case.escalated", result)
            if result.get("risk_level") == "high":
                webhook_dispatcher.dispatch_event("fraud.alert", result)

            self.processed_count += 1
            return result
        except Exception as exc:
            return {"error": str(exc), "transaction_id": tx_id}

    def process_one_now(self) -> dict[str, Any] | None:
        """Synchronously process a single queued message (useful for tests and manual pumps)."""
        msg = self.broker.consume(block=False)
        if msg:
            return self._process_message(msg)
        return None


# Global worker instance
queue_worker = ConsumerWorker(auto_start=False)
