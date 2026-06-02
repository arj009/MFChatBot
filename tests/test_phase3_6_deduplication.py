"""Tests for Phase 3.6 Deduplication & Context Formatting."""

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


def test_retriever_deduplication(tmp_path):
    # Setup test collection
    test_db_dir = tmp_path / "test_index"
    collection = MFVectorStore.get_collection(test_db_dir)

    # 1. Prepare 4 chunks where 2 chunks belong to URL 1, 1 belongs to URL 2, 1 belongs to URL 3
    docs = [
        "URL1 chunk A: SIP basic rules and minimum investment limits.",
        "URL1 chunk B: SIP recurring investment options and benefits.",
        "URL2 chunk A: Exit load constraints and taxation rules.",
        "URL3 chunk A: Expense ratios for mutual fund schemes.",
    ]
    ids = ["url1_a", "url1_b", "url2_a", "url3_a"]
    
    metadatas = [
        {"source_url": "https://groww.in/url1", "scheme_slug": "fund1", "chunk_index": 0},
        {"source_url": "https://groww.in/url1", "scheme_slug": "fund1", "chunk_index": 1},
        {"source_url": "https://groww.in/url2", "scheme_slug": "fund2", "chunk_index": 0},
        {"source_url": "https://groww.in/url3", "scheme_slug": "fund3", "chunk_index": 0},
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

    # 2. Query WITHOUT deduplication: should return multiple chunks from URL 1
    raw_results = retriever.retrieve("SIP options", top_k=3, deduplicate=False)
    # At least two of the results should be from url1
    url1_hits = [r for r in raw_results if r["metadata"]["source_url"] == "https://groww.in/url1"]
    assert len(url1_hits) >= 2

    # 3. Query WITH deduplication: should return at most one chunk per unique source_url
    dedup_results = retriever.retrieve("SIP options", top_k=3, deduplicate=True)
    
    # Assert length is limited to top_k
    assert len(dedup_results) <= 3
    
    # Assert all source_urls in the results list are unique
    seen_urls = set()
    for item in dedup_results:
        url = item["metadata"]["source_url"]
        assert url not in seen_urls, f"Duplicate URL citation found in dedup results: {url}"
        seen_urls.add(url)

    # 4. Verify helper function level support
    helper_results = retrieve("SIP options", top_k=2, deduplicate=True, index_dir=test_db_dir)
    assert len(helper_results) <= 2
    seen_urls_helper = set()
    for item in helper_results:
        url = item["metadata"]["source_url"]
        assert url not in seen_urls_helper
        seen_urls_helper.add(url)
