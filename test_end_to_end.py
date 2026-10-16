
from agent.agent import process_complaint


def main():
    complaint = (
        "I did not authorize this transaction. "
        "Please investigate it immediately."
    )
    transaction_id = "TX1001"

    result = process_complaint(
        complaint_text=complaint,
        transaction_id=transaction_id,
    )

    print("\n--- End-to-End Triage Result ---")
    for key, value in result.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()
