
import pandas as pd

from agent.tools import check_fraud_score
from ml.fraud_model import FEATURE_NAMES


def test_fraud_model_adapter_with_real_dataset_rows():
    # Load two examples from the actual dataset:
    # one normal transaction and one fraudulent transaction.
    df = pd.read_csv("data/creditcard.csv")

    feature_columns = FEATURE_NAMES

    normal_row = df[df["Class"] == 0].iloc[0]
    fraud_row = df[df["Class"] == 1].iloc[0]

    for row in [normal_row, fraud_row]:
        transaction = {
            "transaction_id": "TEST_TRANSACTION",
            "model_features": {
                name: float(row[name])
                for name in feature_columns
            },
        }

        result = check_fraud_score(transaction)

        assert result["error"] is None
        assert result["fraud_probability"] is not None
        assert result["risk_level"] in {"low", "medium", "high"}

        print(
            f"Actual class: {int(row['Class'])} | "
            f"Model output: {result}"
        )


if __name__ == "__main__":
    test_fraud_model_adapter_with_real_dataset_rows()
    print("Fraud model adapter integration test passed.")
