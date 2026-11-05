"""
duplicate_tool.py — Duplicate Transaction Detection Tool
Detects potential duplicate charges (same amount, merchant, customer) within a time window.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any
from .transaction_tool import get_transaction, load_all_transactions


def check_duplicate_transactions(transaction_id: str, window_minutes: int = 10) -> list[dict[str, Any]]:
    """Find potential duplicate transactions within the specified minute window."""
    target_tx = get_transaction(transaction_id)
    if target_tx is None or not target_tx.get("timestamp"):
        return []

    try:
        target_time = datetime.fromisoformat(target_tx["timestamp"])
    except (ValueError, TypeError):
        return []

    matches = []
    delta = timedelta(minutes=window_minutes)

    for other in load_all_transactions():
        if other.get("transaction_id") == transaction_id:
            continue
        if other.get("customer_id") != target_tx.get("customer_id"):
            continue
        if other.get("amount") != target_tx.get("amount"):
            continue
        if other.get("currency") != target_tx.get("currency"):
            continue
        if other.get("merchant") != target_tx.get("merchant"):
            continue

        try:
            other_time = datetime.fromisoformat(other["timestamp"])
            if abs(other_time - target_time) <= delta:
                matches.append(other)
        except (ValueError, TypeError):
            continue

    return matches


def find_possible_duplicates_tool(transaction_id: str, window_minutes: int = 10) -> dict[str, Any]:
    """Agent tool wrapper for duplicate transaction detection."""
    duplicates = check_duplicate_transactions(transaction_id, window_minutes)
    return {
        "transaction_id": transaction_id,
        "duplicate_count": len(duplicates),
        "potential_duplicates": [
            {
                "transaction_id": d.get("transaction_id"),
                "amount": d.get("amount"),
                "merchant": d.get("merchant"),
                "timestamp": d.get("timestamp"),
            }
            for d in duplicates
        ],
    }
