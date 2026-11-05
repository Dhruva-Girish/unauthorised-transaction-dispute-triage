"""
webhook_manager.py — Webhook Subscription Registry & HMAC Security (Unit 1.C & 2.F)
Manages webhook endpoints, subscriptions, and cryptographic HMAC-SHA256 signatures.
"""

from __future__ import annotations

import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class WebhookManager:
    """Manages active webhook endpoint subscriptions."""

    def __init__(self) -> None:
        self.subscriptions: dict[str, dict[str, Any]] = {}

    def register_webhook(
        self,
        target_url: str,
        events: list[str],
        secret: str | None = None,
    ) -> dict[str, Any]:
        """Register a new webhook subscription."""
        sub_id = f"WH-{uuid4().hex[:8].upper()}"
        sec = secret or uuid4().hex
        sub = {
            "subscription_id": sub_id,
            "target_url": target_url,
            "events": events,
            "secret": sec,
            "active": True,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        self.subscriptions[sub_id] = sub
        return sub

    def list_subscriptions(self) -> list[dict[str, Any]]:
        """Return list of active subscriptions."""
        return list(self.subscriptions.values())

    @staticmethod
    def sign_payload(payload_bytes: bytes | str, secret: str) -> str:
        """Generate HMAC-SHA256 signature for webhook verification."""
        if isinstance(payload_bytes, str):
            payload_bytes = payload_bytes.encode("utf-8")
        return hmac.new(secret.encode("utf-8"), payload_bytes, hashlib.sha256).hexdigest()

    generate_signature = sign_payload

    @classmethod
    def verify_signature(cls, payload_bytes: bytes | str, secret: str, signature: str | None = None) -> bool:
        """Verify HMAC-SHA256 signature matches payload."""
        if signature is None and isinstance(secret, str):
            # In case args were passed (payload, signature, secret)
            pass
        if isinstance(payload_bytes, str):
            payload_bytes = payload_bytes.encode("utf-8")
        expected = cls.sign_payload(payload_bytes, secret)
        return hmac.compare_digest(expected, signature if signature else "")


# Global webhook manager
webhook_manager = WebhookManager()
