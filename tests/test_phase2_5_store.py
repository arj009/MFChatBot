"""Tests for Phase 2.5 chunk store persistence."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_4_chunk.chunker import chunk_all  # noqa: E402
from src.ingestion.phase_2_5_store.store import persist_chunks, validate_phase2_5  # noqa: E402
from src.ingestion.shared.paths import CHUNK_STORE_PATH  # noqa: E402


def test_persist_chunks_flow():
    # 1. Generate all in-memory chunks
    chunks = chunk_all()
    assert len(chunks) > 0

    # 2. Persist them
    persist_chunks(chunks)
    assert CHUNK_STORE_PATH.is_file()

    # 3. Validate the store
    ok, errors = validate_phase2_5()
    assert ok is True, f"Validation failed: {errors}"


def test_persist_rejects_off_list():
    chunks = chunk_all()
    if not chunks:
        pytest.skip("No chunks generated to test with.")

    # Mutate a chunk to reference an off-list URL
    bad_chunk = chunks[0].copy()
    bad_chunk["source_url"] = "https://example.com/off-list-mutual-fund"

    # Verify that trying to persist it raises ValueError
    with pytest.raises(ValueError) as excinfo:
        persist_chunks([bad_chunk])
    assert "references off-list or missing URL" in str(excinfo.value)
