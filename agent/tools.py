
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

DATA_FILE = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "transactions.json"
)


def load_transactions() -> list[dict[str, Any]]:
    """Load transaction records from JSON."""
    with DATA_FILE.open("r", encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise ValueError("Transaction data must be a JSON list.")

    return records


def get_transaction(transaction_id: str) -> dict | None:
    """Retrieve one transaction by ID."""
    for transaction in load_transactions():
        if transaction.get("transaction_id") == transaction_id:
            return transaction

    return None


def get_transaction_history(
    customer_id: str,
    exclude_transaction_id: str | None = None,
) -> list[dict]:
    """Retrieve other transactions belonging to a customer."""
    return [
        transaction
        for transaction in load_transactions()
        if transaction.get("customer_id") == customer_id
        and transaction.get("transaction_id")
        != exclude_transaction_id
    ]


def check_duplicate_transactions(
    transaction_id: str,
) -> list[dict]:
    """Find possible duplicates within a ten-minute window."""
    transaction = get_transaction(transaction_id)

    if transaction is None:
        return []

    target_time = datetime.fromisoformat(transaction["timestamp"])
    matches = []

    for other in load_transactions():
        if other["transaction_id"] == transaction_id:
            continue

        if other.get("customer_id") != transaction.get("customer_id"):
            continue

        if other.get("amount") != transaction.get("amount"):
            continue

        if other.get("currency") != transaction.get("currency"):
            continue

        if other.get("merchant") != transaction.get("merchant"):
            continue

        other_time = datetime.fromisoformat(other["timestamp"])

        if abs(other_time - target_time) <= timedelta(minutes=10):
            matches.append(other)

    return matches


def check_fraud_score(transaction: dict) -> dict:
    """
    Temporary adapter for Member 1's ML model.
    Does not invent a prediction when features are unavailable.
    """
    features = transaction.get("model_features")

    if not isinstance(features, dict):
        return {
            "fraud_probability": None,
            "risk_level": "unavailable",
            "error": "Model features are not available.",
        }

    try:
        # Update this import after Member 1 finalizes their interface.
        from ml.fraud_model import predict_fraud

        result = predict_fraud(features)

        return {
            "fraud_probability": result["fraud_probability"],
            "risk_level": result["risk_level"],
            "error": None,
        }

    except (ImportError, FileNotFoundError, ValueError, KeyError) as exc:
        return {
            "fraud_probability": None,
            "risk_level": "unavailable",
            "error": f"Fraud assessment unavailable: {exc}",
        }
