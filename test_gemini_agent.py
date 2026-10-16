
from agent.agent import process_complaint

test_cases = [
    {
        "name": "Unauthorized transaction",
        "complaint": "I did not authorize this payment. It is not mine.",
        "transaction_id": "TX1001",
        "expected_category": "unauthorized_transaction",
    },
    {
        "name": "Possible duplicate payment",
        "complaint": "I was charged twice for the same purchase.",
        "transaction_id": "TX1002",
        "expected_category": "duplicate_payment",
    },
    {
        "name": "Goods not received",
        "complaint": "My order was never delivered.",
        "transaction_id": "TX1002",
        "expected_category": "goods_not_received",
    },
]

for test in test_cases:
    print(f"\n{'=' * 55}")
    print(f"Test: {test['name']}")

    result = process_complaint(
        complaint_text=test["complaint"],
        transaction_id=test["transaction_id"],
    )

    print("Category:", result["complaint_category"])
    print("Priority:", result["priority"])
    print("Human review:", result["requires_human_review"])
    print("Status:", result["status"])
    print("Error:", result.get("error"))

    assert (
        result["complaint_category"] == test["expected_category"]
    ), f"Unexpected category for {test['name']}"

    assert result["requires_human_review"] is True
    assert result["status"] == "under_review"

print("\nAll complaint workflow tests passed.")
