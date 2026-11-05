"""
imbalance_handler.py — Class Imbalance Handling Strategies (Unit 1.A & Person 1)
Supports cost-sensitive reweighting, random undersampling, and SMOTE oversampling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.utils.class_weight import compute_class_weight


def get_class_weights(y: pd.Series | np.ndarray) -> dict[int, float]:
    """Compute balanced class weights for cost-sensitive learning."""
    classes = np.unique(y)
    weights = compute_class_weight(class_weight="balanced", classes=classes, y=y)
    return {int(cls): float(weight) for cls, weight in zip(classes, weights)}


def handle_class_imbalance(
    X: pd.DataFrame,
    y: pd.Series,
    method: str = "smote",
    random_state: int = 42,
) -> tuple[pd.DataFrame, pd.Series]:
    """
    Handle extreme fraud class imbalance.
    Methods:
      - 'smote': Synthetic Minority Over-sampling Technique
      - 'undersample': Controlled majority class undersampling
      - 'passthrough': Return unchanged (to rely on class_weight='balanced')
    """
    method = method.lower()

    if method == "smote":
        try:
            from imblearn.over_sampling import SMOTE
            # Ensure minority count is enough for k_neighbors
            minority_count = (y == 1).sum()
            k_neighbors = min(5, max(1, minority_count - 1))
            smote = SMOTE(k_neighbors=k_neighbors, random_state=random_state)
            X_res, y_res = smote.fit_resample(X, y)
            return pd.DataFrame(X_res, columns=X.columns), pd.Series(y_res, name=y.name)
        except (ImportError, ValueError):
            # Graceful fallback to passthrough with balanced weights
            return X, y

    elif method == "undersample":
        try:
            from imblearn.under_sampling import RandomUnderSampler
            rus = RandomUnderSampler(random_state=random_state)
            X_res, y_res = rus.fit_resample(X, y)
            return pd.DataFrame(X_res, columns=X.columns), pd.Series(y_res, name=y.name)
        except ImportError:
            return X, y

    return X, y
