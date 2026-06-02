"""Phase 3.1 — Embedding Model Selection & Configuration.

Provides local, CPU-friendly SentenceTransformer utilities for text chunk vectorization.
(Forwarding import for backward compatibility)
"""

from src.retrieval.phase_3_1_embed.embedder import MFEmbedder

__all__ = ["MFEmbedder"]
