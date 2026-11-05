"""
chunker.py — Document Ingestion and Chunking Engine (Unit 3.C)
Chunks policy documentation into overlapping semantic passages with metadata.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class DocumentChunk:
    chunk_id: str
    content: str
    source_file: str
    section_title: str
    metadata: dict[str, str] = field(default_factory=dict)


def chunk_markdown_document(
    file_path: Path | str,
    max_chunk_chars: int = 500,
    overlap_chars: int = 50,
) -> list[DocumentChunk]:
    """Split markdown documents by headers and sliding window chunks."""
    path = Path(file_path)
    if not path.exists():
        return []

    text = path.read_text(encoding="utf-8")
    sections = re.split(r"(^##\s+.+$)", text, flags=re.MULTILINE)

    chunks: list[DocumentChunk] = []
    current_title = path.stem.replace("_", " ").title()
    chunk_counter = 0

    for i in range(len(sections)):
        part = sections[i].strip()
        if not part:
            continue
        if part.startswith("##"):
            current_title = part.lstrip("#").strip()
            continue

        # Split passage into overlapping chunks if too long
        if len(part) <= max_chunk_chars:
            chunk_counter += 1
            chunks.append(
                DocumentChunk(
                    chunk_id=f"{path.stem}_{chunk_counter:03d}",
                    content=part,
                    source_file=path.name,
                    section_title=current_title,
                )
            )
        else:
            start = 0
            while start < len(part):
                end = min(start + max_chunk_chars, len(part))
                sub_text = part[start:end].strip()
                if sub_text:
                    chunk_counter += 1
                    chunks.append(
                        DocumentChunk(
                            chunk_id=f"{path.stem}_{chunk_counter:03d}",
                            content=sub_text,
                            source_file=path.name,
                            section_title=current_title,
                        )
                    )
                start += max_chunk_chars - overlap_chars

    return chunks
