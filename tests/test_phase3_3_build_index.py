"""Tests for Phase 3.3 Index Builder CLI."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.build_index import build_index  # noqa: E402
from src.retrieval.store import MFVectorStore  # noqa: E402


@pytest.fixture(autouse=True)
def reset_store_singleton():
    # Clear store clients before and after to avoid SQLite lock issues
    MFVectorStore._client = None
    yield
    MFVectorStore._client = None


def test_build_index_dry_run(tmp_path):
    # Setup temporary store and index paths
    mock_store = tmp_path / "mock_store.jsonl"
    mock_index_dir = tmp_path / "mock_index"

    # Create dummy chunk
    chunk = {
        "source_url": "https://groww.in/mutual-funds/test-fund",
        "source_type": "scheme_page",
        "amc": "ICICI Prudential Mutual Fund",
        "scheme_name": "Test Fund",
        "scheme_slug": "test-fund",
        "scheme_category": "equity",
        "document_title": "Test Fund NAV",
        "last_fetched_at": "2026-05-18T12:00:00+00:00",
        "content_hash": "mockhash123",
        "chunk_index": 0,
        "text": "This is a mock fund test sentence for indexing.",
    }
    mock_store.write_text(json.dumps(chunk) + "\n", encoding="utf-8")

    # Run dry run
    code = build_index(
        store_path=mock_store,
        index_dir=mock_index_dir,
        dry_run=True,
    )
    
    assert code == 0
    # In dry run, database folder should not contain Chroma SQLite files
    sqlite_file = mock_index_dir / "chroma.sqlite3"
    assert not sqlite_file.exists()


def test_build_index_full_execution(tmp_path):
    # Setup paths
    mock_store = tmp_path / "mock_store.jsonl"
    mock_index_dir = tmp_path / "mock_index"

    # Create 2 dummy chunks, one with None fields
    chunk_1 = {
        "source_url": "https://groww.in/mutual-funds/test-fund-1",
        "source_type": "scheme_page",
        "amc": "ICICI Prudential Mutual Fund",
        "scheme_name": "Test Fund 1",
        "scheme_slug": "test-fund-1",
        "scheme_category": "equity",
        "document_title": "Test Fund 1 NAV",
        "last_fetched_at": "2026-05-18T12:00:00+00:00",
        "content_hash": "mockhash123",
        "chunk_index": 0,
        "text": "First mock text details regarding SIP constraints.",
    }
    chunk_2 = {
        "source_url": "https://groww.in/mutual-funds/test-fund-2",
        "source_type": "scheme_page",
        "amc": None,  # Mocking a None value
        "scheme_name": None,
        "scheme_slug": "test-fund-2",
        "scheme_category": None,
        "document_title": "Test Fund 2 NAV",
        "last_fetched_at": "2026-05-18T12:00:00+00:00",
        "content_hash": "mockhash456",
        "chunk_index": 0,
        "text": "Second mock text details regarding exit loads.",
    }

    with mock_store.open("w", encoding="utf-8") as f:
        f.write(json.dumps(chunk_1) + "\n")
        f.write(json.dumps(chunk_2) + "\n")

    # Run complete index compilation
    code = build_index(
        store_path=mock_store,
        index_dir=mock_index_dir,
        dry_run=False,
    )

    assert code == 0
    assert mock_index_dir.exists()

    # Re-retrieve collection and inspect entries
    collection = MFVectorStore.get_collection(mock_index_dir)
    assert collection.count() == 2

    # Check that None values were safely converted to "" (empty strings) rather than crashing Chroma
    results = collection.get(ids=["c_001_test-fund-2_ch0"])
    assert results is not None
    assert len(results["metadatas"]) == 1
    meta = results["metadatas"][0]
    
    assert meta["amc"] == ""
    assert meta["scheme_name"] == ""
    assert meta["scheme_category"] == ""
    assert meta["scheme_slug"] == "test-fund-2"
