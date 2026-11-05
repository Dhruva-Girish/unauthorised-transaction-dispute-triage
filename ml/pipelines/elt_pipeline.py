"""
elt_pipeline.py — Extract-Load-Transform Pipeline (Unit 1.D)
Extracts raw events, loads them unadulterated into a Bronze data layer,
and runs transformations inside the analytical storage layer (Silver/Gold pattern).
"""

from __future__ import annotations

import sqlite3
import time
from pathlib import Path
from typing import Any
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent


class ELTPipeline:
    """Demonstrates ELT pattern (modern data lakehouse architecture)."""

    def __init__(self, db_path: Path | str | None = None) -> None:
        self.db_path = Path(db_path) if db_path else ROOT / "data" / "lakehouse_elt.db"
        self.metrics: dict[str, Any] = {}

    def extract_and_load_bronze(self, raw_csv_path: Path | str | None = None) -> int:
        """Extract raw records and immediately load into Bronze raw table."""
        start = time.perf_counter()
        csv_path = Path(raw_csv_path) if raw_csv_path else ROOT / "data" / "creditcard_sample.csv"
        df = pd.read_csv(csv_path)

        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(self.db_path) as conn:
            # Bronze: Raw, unvalidated landing table
            df.to_sql("bronze_raw_transactions", conn, if_exists="replace", index=False)

        self.metrics["extract_load_bronze_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
        self.metrics["bronze_record_count"] = len(df)
        return len(df)

    def transform_in_place_silver_gold(self) -> dict[str, int]:
        """Transform inside the database engine: filter anomalies into Silver, aggregate into Gold."""
        start = time.perf_counter()
        with sqlite3.connect(self.db_path) as conn:
            # Silver: Cleaned, validated table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS silver_clean_transactions AS
                SELECT * FROM bronze_raw_transactions
                WHERE Amount >= 0.0 AND Time IS NOT NULL
            """)

            # Gold: Aggregated feature tables for analytics and modeling
            conn.execute("""
                CREATE TABLE IF NOT EXISTS gold_fraud_summary AS
                SELECT
                    Class,
                    COUNT(*) as tx_count,
                    AVG(Amount) as avg_amount,
                    MAX(Amount) as max_amount,
                    MIN(Amount) as min_amount
                FROM silver_clean_transactions
                GROUP BY Class
            """)

            cur = conn.cursor()
            cur.execute("SELECT COUNT(*) FROM silver_clean_transactions")
            silver_count = cur.fetchone()[0]

            cur.execute("SELECT COUNT(*) FROM gold_fraud_summary")
            gold_count = cur.fetchone()[0]

        self.metrics["transform_silver_gold_ms"] = round((time.perf_counter() - start) * 1000.0, 2)
        return {"silver_records": silver_count, "gold_records": gold_count}

    def run(self) -> dict[str, Any]:
        """Execute complete ELT workflow."""
        start = time.perf_counter()
        bronze_count = self.extract_and_load_bronze()
        layers = self.transform_in_place_silver_gold()
        total_ms = round((time.perf_counter() - start) * 1000.0, 2)
        return {
            "status": "SUCCESS",
            "pipeline_type": "ELT",
            "total_latency_ms": total_ms,
            "bronze_records": bronze_count,
            "silver_records": layers["silver_records"],
            "gold_records": layers["gold_records"],
            "metrics": self.metrics,
            "db_path": str(self.db_path),
        }
