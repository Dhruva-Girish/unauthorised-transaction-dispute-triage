"""
data_validator.py — Ingestion Validation and Schema Consistency Checks (Unit 1.D)
Validates input schemas, data types, nulls, value boundaries, and contract integrity.
"""

from __future__ import annotations

from typing import Any
import math
import pandas as pd

REQUIRED_FEATURES = ["Time"] + [f"V{i}" for i in range(1, 29)] + ["Amount"]


def validate_feature_vector(features: dict[str, Any]) -> tuple[bool, list[str]]:
    """
    Validate a single feature dictionary against model schema contracts.
    Returns (is_valid, list_of_error_messages).
    """
    errors: list[str] = []

    missing = set(REQUIRED_FEATURES) - set(features.keys())
    if missing:
        errors.append(f"Missing required feature(s): {sorted(missing)}")

    extra = set(features.keys()) - set(REQUIRED_FEATURES)
    if extra:
        errors.append(f"Unexpected extra feature(s): {sorted(extra)}")

    for name in REQUIRED_FEATURES:
        if name in features:
            val = features[name]
            if val is None:
                errors.append(f"Feature '{name}' cannot be null.")
            elif not isinstance(val, (int, float)):
                try:
                    val = float(val)
                except (ValueError, TypeError):
                    errors.append(f"Feature '{name}' must be numeric, got {type(val).__name__}.")
                    continue
            try:
                if not math.isfinite(float(val)):
                    errors.append(f"Feature '{name}' must be finite.")
            except (ValueError, TypeError, OverflowError):
                errors.append(f"Feature '{name}' must be numeric, got {type(val).__name__}.")

    if "Amount" in features and features["Amount"] is not None:
        try:
            amt = float(features["Amount"])
            if amt < 0.0:
                errors.append(f"Amount cannot be negative: got {amt}")
        except (ValueError, TypeError):
            pass

    return len(errors) == 0, errors


def validate_ingestion_data(df: pd.DataFrame, is_training: bool = False) -> dict[str, Any]:
    """
    Validate a batch or dataset at ingestion.
    Checks schema consistency, missingness, duplicate rows, and value ranges.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if df.empty:
        return {
            "is_valid": False,
            "row_count": 0,
            "errors": ["Ingestion batch is empty."],
            "warnings": [],
        }

    # Schema consistency
    expected_cols = REQUIRED_FEATURES + (["Class"] if is_training else [])
    missing_cols = set(expected_cols) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required column(s): {sorted(missing_cols)}")

    # Null value inspection
    null_counts = df.isnull().sum()
    cols_with_nulls = null_counts[null_counts > 0]
    if not cols_with_nulls.empty:
        errors.append(f"Null values detected in columns: {cols_with_nulls.to_dict()}")

    # Boundary checks
    if "Amount" in df.columns:
        negative_amounts = (df["Amount"] < 0).sum()
        if negative_amounts > 0:
            errors.append(f"Detected {negative_amounts} negative Amount values.")

    # Duplicate check
    duplicate_count = df.duplicated().sum()
    if duplicate_count > 0:
        warnings.append(f"Detected {duplicate_count} duplicate row(s) in ingestion batch.")

    if is_training and "Class" in df.columns:
        unique_classes = set(df["Class"].unique())
        if not unique_classes.issubset({0, 1}):
            errors.append(f"Target 'Class' column contains invalid labels: {unique_classes}")

    return {
        "is_valid": len(errors) == 0,
        "row_count": len(df),
        "column_count": len(df.columns),
        "errors": errors,
        "warnings": warnings,
    }
