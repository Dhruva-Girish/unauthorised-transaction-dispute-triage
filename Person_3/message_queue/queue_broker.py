"""
queue_broker.py — Asynchronous Message Queue Broker (Unit 1.B & 1.C)
Provides thread-safe FIFO message queueing for asynchronous dispute ingestion and event decoupling.
"""

from __future__ import annotations

import json
import queue
import time
from typing import Any
from uuid import uuid4


class MessageQueueBroker:
    """Thread-safe in-memory message queue broker supporting producer-consumer patterns."""

    def __init__(self, maxsize: int = 10000) -> None:
        self._queue: queue.Queue = queue.Queue(maxsize=maxsize)
        self.published_count = 0
        self.consumed_count = 0

    def publish(self, topic: str, payload: dict[str, Any]) -> str:
        """Publish a message to a topic."""
        msg_id = f"MSG-{uuid4().hex[:8].upper()}"
        envelope = {
            "msg_id": msg_id,
            "message_id": msg_id,
            "topic": topic,
            "timestamp": time.time(),
            "payload": payload,
        }
        self._queue.put(envelope, block=True, timeout=5.0)
        self.published_count += 1
        return msg_id

    def consume(self, block: bool = True, timeout: float = 1.0) -> dict[str, Any] | None:
        """Consume the next available message from the queue."""
        try:
            msg = self._queue.get(block=block, timeout=timeout)
            self.consumed_count += 1
            self._queue.task_done()
            return msg
        except queue.Empty:
            return None

    def size(self) -> int:
        """Return the current depth of pending messages in the queue."""
        return self._queue.qsize()

    get_queue_length = size
    get_pending_count = size

    def stats(self) -> dict[str, Any]:
        """Return operational queue metrics."""
        return {
            "pending_messages": self.size(),
            "published_total": self.published_count,
            "consumed_total": self.consumed_count,
        }


# Global message queue broker
message_broker = MessageQueueBroker()
