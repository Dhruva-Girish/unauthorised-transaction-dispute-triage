"""
data_cleaner.py — Data Preprocessing and Cleaning Utilities
"""

from __future__ import annotations

import pandas as pd
from sklearn.preprocessing import StandardScaler


def clean_transaction_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize transaction data: drop duplicate transactions, coerce numeric types,
    and fill minor numerical voids with column medians.
    """
    clean_df = df.copy()

    # Drop exact duplicates if any
    clean_df = clean_df.drop_duplicates()

    # Coerce numeric columns
    for col in clean_df.columns:
        if col not in ["transaction_id", "customer_id", "timestamp", "country", "merchant", "currency"]:
            clean_df[col] = pd.to_numeric(clean_df[col], errors="coerce")

    # Median imputation for any residual nulls
    clean_df = clean_df.fillna(clean_df.median(numeric_only=True))

    return clean_df


def scale_numerical_features(
    df: pd.DataFrame,
    feature_cols: list[str] | None = None,
    scaler: StandardScaler | None = None,
) -> tuple[pd.DataFrame, StandardScaler]:
    """
    Scale numeric features (Time and Amount) while preserving anonymized PCA features.
    """
    scaled_df = df.copy()
    feature_cols = feature_cols or ["Time", "Amount"]

    if scaler is None:
        scaler = StandardScaler()
        scaled_df[feature_cols] = scaler.fit_transform(scaled_df[feature_cols])
    else:
        scaled_df[feature_cols] = scaler.transform(scaled_df[feature_cols])

    return scaled_df, scaler
