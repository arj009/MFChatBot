"""Tests for Phase 3.4 Basic Semantic Retriever API."""

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


def test_retrieve_empty_collection(tmp_path):
    # Verify retrieving from empty collection is handled gracefully
    test_db_dir = tmp_path / "test_index"
    retriever = MFRetriever(index_dir=test_db_dir)
    
    results = retriever.retrieve("recurring payment", top_k=3)
    assert results == []


def test_semantic_retrieval_ranking(tmp_path):
    # Setup test collection
    test_db_dir = tmp_path / "test_index"
    collection = MFVectorStore.get_collection(test_db_dir)

    # 1. Prepare dummy data
    docs = [
        "Minimum SIP investment is 100 rupees. Recurring investments are encouraged.",
        "Exit load of 1% is charged if you redeem your units within 15 days.",
        "Tax implications on capital gains: short-term capital gains tax is 15%.",
    ]
    ids = ["doc_sip", "doc_exit", "doc_tax"]
    metadatas = [
        {"source_url": "https://groww.in/sip", "scheme_slug": "sip-fund", "chunk_index": 0},
        {"source_url": "https://groww.in/exit", "scheme_slug": "exit-fund", "chunk_index": 0},
        {"source_url": "https://groww.in/tax", "scheme_slug": "tax-fund", "chunk_index": 0},
    ]

    # Generate embeddings
    embeddings = MFEmbedder.embed_texts(docs)

    # Add to collection
    collection.add(
        ids=ids,
        embeddings=embeddings,
        documents=docs,
        metadatas=metadatas,
    )

    # 2. Test semantic search for "recurring investment" -> should rank SIP highest
    retriever = MFRetriever(index_dir=test_db_dir)
    sip_results = retriever.retrieve("recurring investment", top_k=2)

    assert len(sip_results) == 2
    # The first document (SIP) should be the top hit
    assert sip_results[0]["id"] == "doc_sip"
    assert "Minimum SIP" in sip_results[0]["text"]
    assert isinstance(sip_results[0]["score"], float)
    assert sip_results[0]["metadata"]["scheme_slug"] == "sip-fund"

    # 3. Test semantic search for "redemption charges" -> should rank exit load highest
    exit_results = retriever.retrieve("redemption charges", top_k=1)
    assert len(exit_results) == 1
    assert exit_results[0]["id"] == "doc_exit"
    assert "Exit load" in exit_results[0]["text"]

    # 4. Test package-level helper function 'retrieve'
    helper_results = retrieve("tax on capital gains", top_k=1, index_dir=test_db_dir)
    assert len(helper_results) == 1
    assert helper_results[0]["id"] == "doc_tax"
