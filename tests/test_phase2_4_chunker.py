"""Tests for Phase 2.4 chunker."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import CorpusEntry  # noqa: E402
from src.ingestion.phase_2_4_chunk.chunker import chunk_entry, chunk_all, validate_phase2_4  # noqa: E402


def test_chunk_entry_basic():
    entry = CorpusEntry(
        id=3,
        scheme_name="ICICI Prudential Large Cap Fund Direct Growth",
        category="large_cap",
        url="https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        scheme_slug="icici-prudential-large-cap-fund-direct-growth",
        source_type="scheme_page",
        status="approved",
        last_reviewed="2026-05-18",
    )

    normalized_text = (
        "# ICICI Prudential Large Cap Fund Direct Growth - NAV\n\n"
        "## Key facts\n"
        "Expense ratio: 1.06\n"
        "Exit load: 1%\n\n"
        "## Investment objective\n"
        "The scheme seeks capital appreciation."
    )

    chunks = chunk_entry(
        entry=entry,
        normalized_text=normalized_text,
        document_title="ICICI Prudential Large Cap Fund Direct Growth - NAV",
        last_fetched_at="2026-05-18T12:00:00Z",
        content_hash="mock_hash",
    )

    # We expect 2 chunks, split by "## Key facts" and "## Investment objective"
    assert len(chunks) == 2

    # Verify first chunk
    c0 = chunks[0]
    assert c0["source_url"] == entry.url
    assert c0["source_type"] == entry.source_type
    assert c0["amc"] == "ICICI Prudential Mutual Fund"
    assert c0["scheme_name"] == entry.scheme_name
    assert c0["scheme_slug"] == entry.scheme_slug
    assert c0["scheme_category"] == entry.category
    assert c0["document_title"] == "ICICI Prudential Large Cap Fund Direct Growth - NAV"
    assert c0["last_fetched_at"] == "2026-05-18T12:00:00Z"
    assert c0["content_hash"] == "mock_hash"
    assert c0["chunk_index"] == 0
    assert "## Key facts" in c0["text"]
    assert "# ICICI Prudential Large Cap Fund" in c0["text"]
    assert "Expense ratio: 1.06" in c0["text"]

    # Verify second chunk
    c1 = chunks[1]
    assert c1["chunk_index"] == 1
    assert "## Investment objective" in c1["text"]
    assert "The scheme seeks capital appreciation." in c1["text"]
    assert "# ICICI Prudential Large Cap Fund" in c1["text"]


def test_chunk_all_and_validation():
    # Execute chunk_all to verify it processes all 30 documents correctly
    chunks = chunk_all()
    assert len(chunks) > 30  # Should have at least 1 chunk per document

    # Validate the chunks
    valid, errors = validate_phase2_4(chunks)
    assert valid is True, f"Validation failed with errors: {errors}"
