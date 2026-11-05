"""
store_manager.py — Embedding Management and Vector Index Maintenance (Unit 3.D)
Manages knowledge ingestion, index creation, persistence, and updates.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from rag.chunker import chunk_markdown_document
    from vector_store.chroma_faiss_adapter import VectorStoreAdapter
except ImportError:
    from Person_2.rag.chunker import chunk_markdown_document
    from Person_2.vector_store.chroma_faiss_adapter import VectorStoreAdapter

KB_DIR = ROOT / "rag" / "knowledge_base"


class VectorStoreManager:
    """Coordinates embedding generation, index persistence, and retrieval updates."""

    def __init__(self, backend: str = "faiss") -> None:
        self.adapter = VectorStoreAdapter(backend=backend)
        self.indexed_files: set[str] = set()

    def build_index_from_knowledge_base(self, kb_path: Path | str | None = None) -> int:
        """Scan knowledge base directory, chunk all policy docs, and populate index."""
        path = Path(kb_path) if kb_path else KB_DIR
        if not path.exists():
            return 0

        total_chunks = 0
        for md_file in path.glob("*.md"):
            chunks = chunk_markdown_document(md_file)
            doc_dicts = [
                {
                    "chunk_id": c.chunk_id,
                    "content": c.content,
                    "source_file": c.source_file,
                    "section_title": c.section_title,
                }
                for c in chunks
            ]
            added = self.adapter.add_documents(doc_dicts)
            self.indexed_files.add(md_file.name)
            total_chunks += added

        return total_chunks

    def search_policy(self, query: str, top_k: int = 2) -> list[dict[str, Any]]:
        """Retrieve relevant dispute policy chunks for a customer complaint."""
        return self.adapter.search(query, top_k=top_k)


# Singleton instance
policy_store = VectorStoreManager(backend="faiss")
# Initialize and index on load
policy_store.build_index_from_knowledge_base()
