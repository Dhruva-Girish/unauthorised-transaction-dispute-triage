
from typing import Any


VALID_CATEGORIES = {
    "unauthorized_transaction",
    "duplicate_payment",
    "goods_not_received",
    "billing_dispute",
    "other",
    "unknown",
}


def create_triage_result(
    case_id: str,
    transaction_id: str,
    complaint_category: str,
    transaction: dict | None,
    fraud_result: dict | None = None,
    duplicate_matches: list[dict] | None = None,
) -> dict[str, Any]:

    fraud_result = fraud_result or {}
    duplicate_matches = duplicate_matches or []

    if complaint_category not in VALID_CATEGORIES:
        complaint_category = "unknown"

    probability = fraud_result.get("fraud_probability")
    risk_level = fraud_result.get("risk_level", "unavailable")

    if transaction is None:
        return {
            "case_id": case_id,
            "transaction_id": transaction_id,
            "complaint_category": complaint_category,
            "fraud_probability": None,
            "risk_level": "unavailable",
            "priority": "review_required",
            "evidence_summary": [],
            "recommended_action": (
                "Request valid transaction information and "
                "review the complaint."
            ),
            "requires_human_review": True,
            "status": "under_review",
            "error": "Transaction not found.",
        }

    evidence = ["Transaction record retrieved successfully."]

    if complaint_category == "unauthorized_transaction":
        evidence.append(
            "Customer reports that they did not authorize the transaction."
        )

        if risk_level == "high":
            priority = "high"
            action = (
                "Prioritize fraud investigation and assess "
                "appropriate card-protection measures."
            )
        else:
            # Never dismiss a fraud complaint solely because
            # the model returns a low score or no score.
            priority = "review_required"
            action = (
                "Investigate the unauthorized-transaction claim "
                "regardless of the model score."
            )

    elif complaint_category == "duplicate_payment":
        if duplicate_matches:
            evidence.append(
                f"{len(duplicate_matches)} possible matching "
                "transaction(s) found."
            )
            priority = "medium"
            action = (
                "Review matching transactions and verify whether "
                "a duplicate charge occurred."
            )
        else:
            priority = "medium"
            action = (
                "Review payment records and request additional "
                "evidence if needed."
            )

    elif complaint_category == "goods_not_received":
        priority = "medium"
        action = (
            "Request order and delivery evidence and route "
            "the case for merchant-dispute review."
        )

    elif complaint_category == "billing_dispute":
        priority = "medium"
        action = "Review the charge and relevant billing records."

    else:
        priority = "review_required"
        action = (
            "Clarify the complaint and route it for appropriate review."
        )

    if probability is not None:
        evidence.append(
            f"Fraud model returned risk level: {risk_level}."
        )
    else:
        evidence.append("Fraud score is unavailable.")

    return {
        "case_id": case_id,
        "transaction_id": transaction_id,
        "complaint_category": complaint_category,
        "fraud_probability": probability,
        "risk_level": risk_level,
        "priority": priority,
        "evidence_summary": evidence,
        "recommended_action": action,
        "requires_human_review": True,
        "status": "under_review",
        "error": None,
    }
