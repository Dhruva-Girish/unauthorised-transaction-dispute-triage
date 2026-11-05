"""
test_rag.py — Tests for Document Ingestion, Chunking, and Vector Retrieval (Unit 3.C)
"""

import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from rag.chunker import chunk_markdown_document
from vector_store.store_manager import policy_store
from rag.rag_pipeline import rag_engine


def test_markdown_chunking():
    policy_doc = ROOT / "rag" / "knowledge_base" / "dispute_policies.md"
    chunks = chunk_markdown_document(policy_doc)
    assert len(chunks) >= 3
    assert all(c.content for c in chunks)
    assert all(c.source_file == "dispute_policies.md" for c in chunks)


def test_vector_search():
    results = policy_store.search_policy("unauthorized card transaction fraud", top_k=2)
    assert len(results) >= 1
    assert "score" in results[0]
    assert "content" in results[0]


def test_rag_context_building():
    context = rag_engine.build_grounded_context(
        complaint_text="I was charged twice.",
        category="duplicate_payment",
        transaction={"transaction_id": "TX1002"},
    )
    assert context["transaction_record_verified"] is True
    assert context["policy_chunk_count"] >= 1
    assert len(context["retrieved_policies"]) >= 1
