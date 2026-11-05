"""Backward-compatible entry point for the Member 1 training pipeline."""

import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ml.training.train_model import main, train_and_evaluate

__all__ = ["main", "train_and_evaluate"]

if __name__ == "__main__":
    train_and_evaluate()
