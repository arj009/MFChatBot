"""Phase 3.2 — Vector Database Configuration & Initialization.

Manages local Chroma DB PersistentClient connections and collections.
"""

from __future__ import annotations

import logging
import pathlib
from typing import ClassVar

import chromadb
from chromadb.config import Settings

__all__ = ["MFVectorStore"]

logger = logging.getLogger("retrieval.store")

DEFAULT_INDEX_DIR = pathlib.Path("data/index")
COLLECTION_NAME = "mf_chunks"


class MFVectorStore:
    """Manages the persistent connection to the local Chroma vector database."""

    _client: ClassVar[chromadb.PersistentClient | None] = None

    @classmethod
    def get_client(cls, path: pathlib.Path | str = DEFAULT_INDEX_DIR) -> chromadb.PersistentClient:
        """Get or initialize a thread-safe singleton persistent Chroma DB client."""
        if cls._client is None:
            db_path = pathlib.Path(path).resolve()
            logger.info(f"Initializing persistent Chroma DB client at '{db_path}'...")
            # PersistentClient writes SQLite metadata and parquet files to local disk
            cls._client = chromadb.PersistentClient(
                path=str(db_path),
                settings=Settings(anonymized_telemetry=False),
            )
        return cls._client

    @classmethod
    def get_collection(
        cls,
        path: pathlib.Path | str = DEFAULT_INDEX_DIR,
    ) -> chromadb.Collection:
        """Retrieve or create the standard mutual fund chunks collection."""
        client = cls.get_client(path)
        logger.debug(f"Getting or creating collection '{COLLECTION_NAME}'...")
        # Since we handle embedding generation in Python (Phase 3.1 MFEmbedder),
        # we configure Chroma collection with no default embedding function (we pass embeddings ourselves)
        return client.get_or_create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"},  # Configure index to use Cosine similarity metric
        )

    @classmethod
    def reset_store(cls, path: pathlib.Path | str = DEFAULT_INDEX_DIR) -> None:
        """Wipe the existing collection to guarantee complete indexing reproducibility."""
        try:
            collection = cls.get_collection(path)
            existing = collection.get()
            if existing and existing.get("ids"):
                logger.info(f"Wiping {len(existing['ids'])} existing chunks from '{COLLECTION_NAME}'...")
                collection.delete(ids=existing["ids"])
                return
        except Exception as e:
            logger.warning(f"Record-based wipe failed: {e}. Falling back to full collection recreate...")

        client = cls.get_client(path)
        try:
            logger.info(f"Wiping existing Chroma collection '{COLLECTION_NAME}' for reconstruction...")
            client.delete_collection(name=COLLECTION_NAME)
        except ValueError:
            # Raised by Chroma if collection does not exist yet; safe to ignore
            logger.debug(f"Collection '{COLLECTION_NAME}' does not exist during wipe.")
        
        # Reset the client singleton to flush database file writes and clear stale cached collection handles
        cls._client = None
        
        # Re-create empty collection
        cls.get_collection(path)
