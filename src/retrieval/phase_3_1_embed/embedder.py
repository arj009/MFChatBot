"""Phase 3.1 — Embedding Model Selection & Configuration.

Provides local, CPU-friendly SentenceTransformer utilities for text chunk vectorization.
"""

from __future__ import annotations

import logging
import time
from typing import ClassVar

from sentence_transformers import SentenceTransformer

__all__ = ["MFEmbedder"]

logger = logging.getLogger("retrieval.embedder")

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
EXPECTED_DIMENSION = 384


class MFEmbedder:
    """Encapsulates local, CPU-friendly SentenceTransformer embedding generation.

    Employs lazy-loading to ensure the underlying deep learning libraries and weights
    are only instantiated when an embedding is first requested.
    """

    _model: ClassVar[SentenceTransformer | None] = None

    @classmethod
    def get_model(cls) -> SentenceTransformer:
        """Lazy-load and return the shared SentenceTransformer model instance."""
        if cls._model is None:
            logger.info(f"Loading embedding model '{MODEL_NAME}'...")
            t0 = time.perf_counter()
            # Loading model onto CPU by default (standard local development scenario)
            cls._model = SentenceTransformer(MODEL_NAME, device="cpu")
            elapsed = time.perf_counter() - t0
            logger.info(f"Loaded '{MODEL_NAME}' successfully in {elapsed:.3f} seconds.")
        return cls._model

    @classmethod
    def embed_text(cls, text: str) -> list[float]:
        """Convert a single text string into a normalized 384-dimensional embedding array."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("Input text must be a non-empty string.")

        model = cls.get_model()
        # normalize_embeddings=True converts outputs to unit length, enabling simple dot product similarity
        embedding = model.encode(text, normalize_embeddings=True, show_progress_bar=False)
        embedding_list = [float(x) for x in embedding]

        if len(embedding_list) != EXPECTED_DIMENSION:
            raise ValueError(
                f"Expected {EXPECTED_DIMENSION} dimensions from model, got {len(embedding_list)}"
            )

        return embedding_list

    @classmethod
    def embed_texts(cls, texts: list[str], show_progress: bool = False) -> list[list[float]]:
        """Batch convert multiple text strings into a list of normalized 384-dimensional arrays."""
        if not isinstance(texts, list) or not all(isinstance(t, str) and t.strip() for t in texts):
            raise ValueError("Input must be a list of non-empty strings.")

        if not texts:
            return []

        model = cls.get_model()
        embeddings = model.encode(
            texts,
            normalize_embeddings=True,
            show_progress_bar=show_progress,
            batch_size=64,
        )

        output: list[list[float]] = []
        for emb in embeddings:
            emb_list = [float(x) for x in emb]
            if len(emb_list) != EXPECTED_DIMENSION:
                raise ValueError(
                    f"Expected {EXPECTED_DIMENSION} dimensions from model, got {len(emb_list)}"
                )
            output.append(emb_list)

        return output
