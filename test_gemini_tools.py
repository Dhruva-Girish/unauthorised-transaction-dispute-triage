
import os
from dotenv import load_dotenv
from google import genai

from agent.tools import get_transaction

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found in .env")

client = genai.Client(api_key=api_key)


def lookup_transaction(transaction_id: str) -> dict:
    """Look up a transaction using its transaction ID.

    Args:
        transaction_id: The transaction ID to look up, such as TX1001.

    Returns:
        The transaction record, or a message if it was not found.
    """
    transaction = get_transaction(transaction_id)

    if transaction is None:
        return {
            "found": False,
            "message": "Transaction not found."
        }

    return {
        "found": True,
        "transaction": transaction
    }


chat = client.chats.create(
    model="gemini-2.5-flash",
    config={
        "tools": [lookup_transaction]
    }
)

response = chat.send_message(
    "The customer says they did not authorize transaction TX1001. "
    "Use the lookup_transaction tool to retrieve the transaction "
    "details. Do not make a fraud decision yet."
)

print("\nGemini's response:")
print(response.text)
