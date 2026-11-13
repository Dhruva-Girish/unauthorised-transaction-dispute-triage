"""
Unit tests for Webhooks: Subscription management, HMAC signature verification, and Dispatcher.
"""
import sys
from pathlib import Path
import pytest
import hmac
import hashlib
import json

ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
P3_PATH = Path(__file__).resolve().parent.parent
if str(P3_PATH) not in sys.path:
    sys.path.insert(0, str(P3_PATH))

try:
    from Person_3.webhooks.webhook_manager import WebhookManager
    from Person_3.webhooks.dispatcher import WebhookDispatcher
except ImportError:
    from webhooks.webhook_manager import WebhookManager
    from webhooks.dispatcher import WebhookDispatcher

def test_webhook_registration_and_signing():
    mgr = WebhookManager()
    sub = mgr.register_webhook("https://example.com/dispute-events", secret="my_test_secret", events=["case.created"])
    assert sub["subscription_id"] is not None
    assert len(mgr.list_subscriptions()) >= 1

    payload = {"event": "case.created", "dispute_id": "DISP-1234"}
    payload_str = json.dumps(payload, sort_keys=True)
    signature = mgr.sign_payload(payload_str, secret="my_test_secret")

    # Verify signature
    expected = hmac.new("my_test_secret".encode(), payload_str.encode(), hashlib.sha256).hexdigest()
    assert signature == expected
    assert mgr.verify_signature(payload_str, secret="my_test_secret", signature=signature) is True
    assert mgr.verify_signature(payload_str, secret="my_test_secret", signature="fake_signature") is False

def test_webhook_dispatcher():
    dispatcher = WebhookDispatcher()
    success = dispatcher.dispatch_event(
        event_type="case.escalated",
        data={"dispute_id": "DISP-5678", "reason": "High fraud probability"}
    )
    assert success is True
