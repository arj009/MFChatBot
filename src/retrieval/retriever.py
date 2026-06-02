"""Phase 3.4 — Basic Semantic Retriever API.

Exposes core Top-k vector nearest-neighbor retrieval over persistent mutual fund chunks.
(Forwarding imports for backward compatibility)
"""

from src.retrieval.phase_3_4_retrieve.retriever import MFRetriever, retrieve

__all__ = ["MFRetriever", "retrieve"]
