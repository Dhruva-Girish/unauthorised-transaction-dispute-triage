"""
transaction_tool.py — Transaction Lookup Tool
Retrieves transaction records by transaction_id from authoritative storage.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
LOCAL_DATA_FILE = ROOT / "data" / "transactions.json"
SHARED_DATA_FILE = ROOT.parent / "Person_3" / "database" / "transactions.json"


def _get_data_path() -> Path:
    if LOCAL_DATA_FILE.exists():
        return LOCAL_DATA_FILE
    if SHARED_DATA_FILE.exists():
        return SHARED_DATA_FILE
    fallback = ROOT.parent.parent / "unauthorised-transaction-dispute-triage" / "data" / "transactions.json"
    if fallback.exists():
        return fallback
    return LOCAL_DATA_FILE


def load_all_transactions() -> list[dict[str, Any]]:
    """Load all transaction ledger records."""
    path = _get_data_path()
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8") as f:
        records = json.load(f)
    return records if isinstance(records, list) else []


def get_transaction(transaction_id: str) -> dict[str, Any] | None:
    """Retrieve one transaction record by ID."""
    for tx in load_all_transactions():
        if tx.get("transaction_id") == transaction_id:
            return tx
    return None


def lookup_transaction_tool(transaction_id: str) -> dict[str, Any]:
    """Agent tool wrapper for transaction lookup."""
    tx = get_transaction(transaction_id)
    if tx is None:
        return {"found": False, "message": f"Transaction '{transaction_id}' not found."}

    return {
        "found": True,
        "transaction_id": tx.get("transaction_id"),
        "amount": tx.get("amount"),
        "currency": tx.get("currency"),
        "merchant": tx.get("merchant"),
        "timestamp": tx.get("timestamp"),
        "customer_id": tx.get("customer_id"),
        "country": tx.get("country"),
        "device_id": tx.get("device_id"),
    }
