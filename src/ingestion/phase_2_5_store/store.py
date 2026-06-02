"""Phase 2.5 — Persist chunk store to a stable JSONL format."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.corpus.inventory import load_inventory
from src.ingestion.phase_2_4_chunk.chunker import chunk_all
from src.ingestion.shared.paths import CHUNKS_DIR, CHUNK_STORE_PATH

__all__ = [
    "persist_chunks",
    "validate_phase2_5",
]

ORDERED_KEYS = [
    "source_url",
    "source_type",
    "amc",
    "scheme_name",
    "scheme_slug",
    "scheme_category",
    "document_title",
    "last_fetched_at",
    "content_hash",
    "chunk_index",
    "text",
]


def persist_chunks(chunks: list[dict[str, Any]]) -> None:
    """Validate and write chunks to a single JSONL file with stable key ordering."""
    entries = load_inventory()
    allowed_urls = {e.url for e in entries}

    # Reject write if any chunk is invalid or references an off-list URL
    for idx, chunk in enumerate(chunks):
        source_url = chunk.get("source_url")
        if not source_url or source_url not in allowed_urls:
            raise ValueError(f"Chunk {idx} references off-list or missing URL: {source_url}")

    # Ensure output directory exists
    CHUNKS_DIR.mkdir(parents=True, exist_ok=True)

    # Write to chunk_store.jsonl with stable key ordering
    with CHUNK_STORE_PATH.open("w", encoding="utf-8") as f:
        for chunk in chunks:
            # Reconstruct the dictionary in strict stable key order
            ordered_chunk = {k: chunk.get(k) for k in ORDERED_KEYS}
            # Append as single line
            f.write(json.dumps(ordered_chunk, ensure_ascii=False) + "\n")


def validate_phase2_5() -> tuple[bool, list[str]]:
    """Validate that the persisted chunk store meets all exit criteria."""
    errors: list[str] = []

    if not CHUNK_STORE_PATH.is_file():
        return False, [f"Missing persisted chunk store file at: {CHUNK_STORE_PATH}"]

    try:
        # Load expected chunks from Phase 2.4 to compare row count and details
        expected_chunks = chunk_all()
    except Exception as e:
        return False, [f"Failed to generate in-memory chunks for comparison: {e}"]

    entries = load_inventory()
    allowed_urls = {e.url for e in entries}

    persisted_chunks: list[dict[str, Any]] = []

    # Read and parse persisted chunks
    with CHUNK_STORE_PATH.open(encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            line_str = line.strip()
            if not line_str:
                continue
            try:
                chunk = json.loads(line_str)
                persisted_chunks.append(chunk)
            except Exception as e:
                errors.append(f"Line {line_num} in chunk store is not valid JSON: {e}")
                return False, errors

    # 1. Row count validation
    if len(persisted_chunks) != len(expected_chunks):
        errors.append(
            f"Row count mismatch: expected {len(expected_chunks)} chunks, found {len(persisted_chunks)} in chunk store"
        )

    # 2. Key ordering, closed list, and value constraints validation
    for idx, c in enumerate(persisted_chunks):
        # Verify key ordering
        actual_keys = list(c.keys())
        if actual_keys != ORDERED_KEYS:
            errors.append(
                f"Chunk {idx} key ordering is not stable.\nExpected: {ORDERED_KEYS}\nFound: {actual_keys}"
            )
            continue

        # Closed corpus check
        url = c["source_url"]
        if url not in allowed_urls:
            errors.append(f"Chunk {idx} references off-list URL: {url}")

        # Text chunk and index checks
        if not c["text"] or not c["text"].strip():
            errors.append(f"Chunk {idx} text is empty")
        if c["chunk_index"] is None:
            errors.append(f"Chunk {idx} chunk_index is missing")

        # Listing checks
        if c["source_type"] == "amc_listing":
            if c["scheme_name"] is not None:
                errors.append(f"Chunk {idx}: amc_listing chunk must have scheme_name: null")
            if c["scheme_category"] is not None:
                errors.append(f"Chunk {idx}: amc_listing chunk must have scheme_category: null")
        else:
            if not c["scheme_name"]:
                errors.append(f"Chunk {idx}: scheme_page chunk must have scheme_name")
            if not c["scheme_category"]:
                errors.append(f"Chunk {idx}: scheme_page chunk must have scheme_category")

    return len(errors) == 0, errors
