"""
features.py — Feast Entities and Feature Views Definition (Unit 1.E)
Defines Feast entities and schemas for offline training and online serving.
"""

from __future__ import annotations
from datetime import timedelta

try:
    from feast import Entity, FeatureView, Field, FileSource
    from feast.types import Float32, Int64, String
    FEAST_INSTALLED = True
except ImportError:
    FEAST_INSTALLED = False

# Entities
if FEAST_INSTALLED:
    customer_entity = Entity(
        name="customer_id",
        value_type=String,
        description="Global Customer Identifier",
    )

    transaction_entity = Entity(
        name="transaction_id",
        value_type=String,
        description="Unique Transaction Identifier",
    )

    # File Sources
    transaction_source = FileSource(
        path="../data/transactions_feast.parquet",
        timestamp_field="event_timestamp",
        created_timestamp_column="created_timestamp",
    )

    # Feature Views
    transaction_fraud_fv = FeatureView(
        name="transaction_fraud_features",
        entities=[transaction_entity],
        ttl=timedelta(days=365),
        schema=[
            Field(name="Time", dtype=Float32),
            Field(name="Amount", dtype=Float32),
        ] + [Field(name=f"V{i}", dtype=Float32) for i in range(1, 29)],
        online=True,
        source=transaction_source,
    )

    customer_spending_fv = FeatureView(
        name="customer_spending_features",
        entities=[customer_entity],
        ttl=timedelta(days=90),
        schema=[
            Field(name="customer_total_spend", dtype=Float32),
            Field(name="customer_tx_count", dtype=Int64),
        ],
        online=True,
        source=transaction_source,
    )
else:
    # Pure python declarative contract representations
    customer_entity = {"name": "customer_id", "type": "String"}
    transaction_entity = {"name": "transaction_id", "type": "String"}
    transaction_fraud_fv = {
        "name": "transaction_fraud_features",
        "entities": ["transaction_id"],
        "features": ["Time", "Amount"] + [f"V{i}" for i in range(1, 29)],
    }
    customer_spending_fv = {
        "name": "customer_spending_features",
        "entities": ["customer_id"],
        "features": ["customer_total_spend", "customer_tx_count"],
    }
