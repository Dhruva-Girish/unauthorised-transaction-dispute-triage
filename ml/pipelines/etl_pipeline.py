"""
etl_pipeline.py — Extract-Transform-Load Pipeline (Unit 1.D)
Extracts raw transaction batches, cleans and transforms features in-memory,
and loads validated records into the feature store / analytics database.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT.parent))

try:
    from ml.preprocessing.data_validator import validate_ingestion_data
    from ml.preprocessing.data_cleaner import clean_transaction_dataframe
except ImportError:
    from ml.preprocessing.data_validator import validate_ingestion_data
    from ml.preprocessing.data_cleaner import clean_transaction_dataframe


class ETLPipeline:
    """Standard ETL Pipeline for transaction data ingestion."""

    def __init__(self, raw_data_path: Path | str | None = None) -> None:
        self.raw_data_path = Path(raw_data_path) if raw_data_path else ROOT / "data" / "creditcard_sample.csv"
        self.metrics: dict[str, Any] = {}

    def extract(self) -> pd.DataFrame:
        """Extract raw records from data source."""
        start = time.perf_counter()
        if not self.raw_data_path.exists():
            raise FileNotFoundError(f"Source data not found at {self.raw_data_path}")
        df = pd.read_csv(self.raw_data_path)
        self.metrics["extract_latency_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
        self.metrics["raw_record_count"] = len(df)
        return df

    def transform(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate contracts, clean values, and engineer feature vectors."""
        start = time.perf_counter()
        # 1. Validation Contract
        val_result = validate_ingestion_data(df, is_training=("Class" in df.columns))
        if not val_result["is_valid"]:
            raise ValueError(f"ETL Validation failed: {val_result['errors']}")

        # 2. Cleaning & Standardization
        clean_df = clean_transaction_dataframe(df)
        self.metrics["transform_latency_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
        self.metrics["clean_record_count"] = len(clean_df)
        return clean_df

    def load(self, df: pd.DataFrame, output_parquet_path: Path | str | None = None) -> Path:
        """Load clean records into target feature storage."""
        start = time.perf_counter()
        out_path = Path(output_parquet_path) if output_parquet_path else ROOT / "data" / "clean_transactions_etl.parquet"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(out_path, index=False)
        self.metrics["load_latency_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
        self.metrics["output_path"] = str(out_path)
        return out_path

    def run(self) -> dict[str, Any]:
        """Execute complete ETL workflow."""
        start = time.perf_counter()
        raw_df = self.extract()
        clean_df = self.transform(raw_df)
        out_path = self.load(clean_df)
        total_ms = round((time.perf_counter() - start) * 1000.0, 2)
        return {
            "status": "SUCCESS",
            "pipeline_type": "ETL",
            "total_latency_ms": total_ms,
            "metrics": self.metrics,
            "output_path": str(out_path),
        }
