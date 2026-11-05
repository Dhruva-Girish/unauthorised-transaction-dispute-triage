"""
rag_pipeline.py — Retrieval-Augmented Generation Engine (Unit 3.C & 3.D)
Combines policy document retrieval with transaction facts to produce grounded recommendations.
Strictly separates external policy knowledge from verified internal transaction ledger records.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from vector_store.store_manager import policy_store
except ImportError:
    from Person_2.vector_store.store_manager import policy_store


class RAGPipeline:
    """Retrieval-Augmented Generation pipeline for dispute resolution."""

    def __init__(self) -> None:
        self.store = policy_store

    def retrieve_relevant_policies(self, complaint_text: str, category: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Retrieve top policy excerpts relevant to the complaint and category."""
        query = f"{category.replace('_', ' ')} {complaint_text}"
        return self.store.search_policy(query, top_k=top_k)

    def build_grounded_context(
        self,
        complaint_text: str,
        category: str,
        transaction: dict[str, Any] | None,
        fraud_score: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Constructs context ensuring clear demarcation between:
        1. Official Policy Guidelines (Retrieved via RAG)
        2. Verified Ledger Records (Transaction DB)
        3. Supervised Model Risk (ML Probability)
        """
        policies = self.retrieve_relevant_policies(complaint_text, category, top_k=2)
        policy_texts = [f"[{p.get('section_title', 'Policy')}]: {p.get('content', '')}" for p in policies]

        return {
            "retrieved_policies": policy_texts,
            "policy_chunk_count": len(policies),
            "transaction_record_verified": transaction is not None,
            "has_fraud_score": fraud_score is not None and fraud_score.get("fraud_probability") is not None,
            "context_summary": (
                f"Retrieved {len(policies)} policy guidelines. "
                f"Ledger record verified: {transaction is not None}. "
                f"ML Risk: {fraud_score.get('risk_level', 'unavailable') if fraud_score else 'none'}."
            ),
        }


# Singleton RAG instance
rag_engine = RAGPipeline()
