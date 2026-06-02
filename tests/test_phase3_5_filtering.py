"""Tests for Phase 3.5 Metadata-Aware Retrieval Filtering."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.retrieval.embedder import MFEmbedder  # noqa: E402
from src.retrieval.retriever import MFRetriever, retrieve  # noqa: E402
from src.retrieval.store import MFVectorStore  # noqa: E402


@pytest.fixture(autouse=True)
def reset_store_singleton():
    # Clear client singleton before and after to ensure isolated test database paths
    MFVectorStore._client = None
    yield
    MFVectorStore._client = None


def test_scheme_hint_filtering(tmp_path):
    # Setup test collection
    test_db_dir = tmp_path / "test_index"
    collection = MFVectorStore.get_collection(test_db_dir)

    # 1. Prepare chunks from two separate real schemes present in url_inventory.csv
    docs = [
        "Large Cap Fund exit load is 1% if redeemed within 1 year.",
        "Technology Fund has a low exit load of 0.5% for redemptions under 30 days.",
    ]
    ids = ["doc_large", "doc_tech"]
    
    # We use exact real-world scheme names & slugs from our closed URL inventory
    metadatas = [
        {
            "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
            "source_type": "scheme_page",
            "amc": "ICICI Prudential Mutual Fund",
            "scheme_name": "ICICI Prudential Large Cap Fund Direct Growth",
            "scheme_slug": "icici-prudential-large-cap-fund-direct-growth",
            "scheme_category": "equity",
            "document_title": "ICICI Prudential Large Cap Fund Direct Growth NAV",
            "last_fetched_at": "2026-05-18T12:00:00+00:00",
            "content_hash": "hash1",
            "chunk_index": 0,
        },
        {
            "source_url": "https://groww.in/mutual-funds/icici-prudential-technology-fund-direct-growth",
            "source_type": "scheme_page",
            "amc": "ICICI Prudential Mutual Fund",
            "scheme_name": "ICICI Prudential Technology Fund Direct Growth",
            "scheme_slug": "icici-prudential-technology-fund-direct-growth",
            "scheme_category": "equity",
            "document_title": "ICICI Prudential Technology Fund Direct Growth NAV",
            "last_fetched_at": "2026-05-18T12:00:00+00:00",
            "content_hash": "hash2",
            "chunk_index": 0,
        },
    ]

    # Generate embeddings and add to DB
    embeddings = MFEmbedder.embed_texts(docs)
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=docs,
        metadatas=metadatas,
    )

    retriever = MFRetriever(index_dir=test_db_dir)

    # 2. Query WITHOUT filtering: both should be returned
    all_results = retriever.retrieve("exit load", top_k=2)
    assert len(all_results) == 2

    # 3. Query WITH scheme_hint = "large" -> should ONLY return Large Cap document
    large_results = retriever.retrieve("exit load", top_k=2, scheme_hint="large")
    assert len(large_results) == 1
    assert large_results[0]["id"] == "doc_large"
    assert "Large Cap Fund" in large_results[0]["text"]
    assert large_results[0]["metadata"]["scheme_slug"] == "icici-prudential-large-cap-fund-direct-growth"

    # 4. Query WITH scheme_hint = "technology" -> should ONLY return Technology document
    tech_results = retriever.retrieve("exit load", top_k=2, scheme_hint="technology")
    assert len(tech_results) == 1
    assert tech_results[0]["id"] == "doc_tech"
    assert "Technology Fund" in tech_results[0]["text"]
    assert tech_results[0]["metadata"]["scheme_slug"] == "icici-prudential-technology-fund-direct-growth"

    # 5. Query WITH exact slug scheme_hint -> should ONLY return Large Cap document
    slug_results = retriever.retrieve("exit load", top_k=2, scheme_hint="icici-prudential-large-cap-fund-direct-growth")
    assert len(slug_results) == 1
    assert slug_results[0]["id"] == "doc_large"

