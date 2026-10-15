import pytest

from ml.fraud_model import predict_fraud, FEATURE_NAMES


def valid_transaction():
    return {name: 0.0 for name in FEATURE_NAMES}


def test_prediction_returns_expected_fields():
    result = predict_fraud(valid_transaction())

    assert set(result.keys()) == {"fraud_probability", "risk_level"}
    assert 0.0 <= result["fraud_probability"] <= 1.0
    assert result["risk_level"] in {"low", "medium", "high"}


def test_missing_feature_raises_error():
    transaction = valid_transaction()
    transaction.pop(FEATURE_NAMES[0])

    with pytest.raises(ValueError, match="Feature mismatch"):
        predict_fraud(transaction)


def test_unexpected_feature_raises_error():
    transaction = valid_transaction()
    transaction["unexpected_feature"] = 1.0

    with pytest.raises(ValueError, match="Feature mismatch"):
        predict_fraud(transaction)


def test_null_feature_raises_error():
    transaction = valid_transaction()
    transaction[FEATURE_NAMES[0]] = None

    with pytest.raises(ValueError, match="null values"):
        predict_fraud(transaction)