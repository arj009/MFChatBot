"""Tests for Phase 3.2 Vector Database Configuration."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import chromadb  # noqa: E402
from src.retrieval.store import MFVectorStore  # noqa: E402


@pytest.fixture(autouse=True)
def reset_singleton():
    # Before test runs: ensure the singleton is empty
    MFVectorStore._client = None
    yield
    # After test runs: clear it again so SQLite database connections are released
    MFVectorStore._client = None


def test_persistent_client_initialization(tmp_path):
    # Verify that get_client initializes persistent storage
    test_db_dir = tmp_path / "test_index"
    client = MFVectorStore.get_client(test_db_dir)
    
    assert client is not None
    # Duck-typing check to verify it behaves like a Client
    assert hasattr(client, "get_or_create_collection")
    assert test_db_dir.exists()


def test_collection_creation(tmp_path):
    # Verify collection retrieval/creation and Cosine config
    test_db_dir = tmp_path / "test_index"
    collection = MFVectorStore.get_collection(test_db_dir)
    
    assert isinstance(collection, chromadb.Collection)
    assert collection.name == "mf_chunks"
    assert collection.metadata is not None
    assert collection.metadata.get("hnsw:space") == "cosine"


def test_store_reset_reproducibility(tmp_path):
    # Add a mock entry to verify collection deletion on reset
    test_db_dir = tmp_path / "test_index"
    collection = MFVectorStore.get_collection(test_db_dir)
    
    # Add dummy item (384 dimensions)
    collection.add(
        ids=["chunk_001"],
        embeddings=[[0.1] * 384],
        documents=["This is a test chunk about exit loads."],
        metadatas=[{"source_url": "https://groww.in/test"}]
    )
    
    # Assert item was written
    assert collection.count() == 1
    
    # Reset store
    MFVectorStore.reset_store(test_db_dir)
    
    # Re-retrieve collection and assert count is zero
    new_collection = MFVectorStore.get_collection(test_db_dir)
    assert new_collection.count() == 0
