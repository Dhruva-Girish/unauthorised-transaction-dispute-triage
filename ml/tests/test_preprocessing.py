"""
test_preprocessing.py — Tests for Data Cleaning and Imbalance Handling
"""

import sys
from pathlib import Path
import pandas as pd
from ml.preprocessing.data_cleaner import clean_transaction_dataframe, scale_numerical_features
from ml.preprocessing.imbalance_handler import get_class_weights, handle_class_imbalance


def test_clean_transaction_dataframe():
    df = pd.DataFrame({
        "transaction_id": ["TX1", "TX1", "TX2"],
        "Amount": ["100.5", "100.5", "50.0"],
        "Time": [1.0, 1.0, None],
    })
    clean = clean_transaction_dataframe(df)
    assert len(clean) == 2  # duplicate removed
    assert clean["Amount"].dtype in [float, "float64"]
    assert clean["Time"].isnull().sum() == 0  # imputed


def test_class_weights_calculation():
    y = pd.Series([0, 0, 0, 0, 1])
    weights = get_class_weights(y)
    assert weights[1] > weights[0]


def test_imbalance_handling_smote():
    X = pd.DataFrame({"V1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0], "Amount": [10.0] * 8})
    y = pd.Series([0, 0, 0, 0, 0, 0, 1, 1], name="Class")
    X_res, y_res = handle_class_imbalance(X, y, method="smote")
    assert len(X_res) >= len(X)
