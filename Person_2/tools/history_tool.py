"""
history_tool.py — Customer Transaction History Retrieval Tool
Retrieves chronological historical transactions for a customer to detect behavioral anomalies.
"""

from __future__ import annotations

from typing import Any
from .transaction_tool import load_all_transactions


def get_customer_history(customer_id: str, exclude_transaction_id: str | None = None) -> list[dict[str, Any]]:
    """Retrieve historical transactions for a customer."""
    all_txs = load_all_transactions()
    return [
        tx for tx in all_txs
        if tx.get("customer_id") == customer_id
        and tx.get("transaction_id") != exclude_transaction_id
    ]


def lookup_customer_history_tool(customer_id: str, exclude_transaction_id: str | None = None) -> dict[str, Any]:
    """Agent tool wrapper for customer history lookup."""
    history = get_customer_history(customer_id, exclude_transaction_id)
    return {
        "customer_id": customer_id,
        "transaction_count": len(history),
        "history": [
            {
                "transaction_id": item.get("transaction_id"),
                "amount": item.get("amount"),
                "currency": item.get("currency"),
                "merchant": item.get("merchant"),
                "timestamp": item.get("timestamp"),
            }
            for item in history
        ],
    }
