"""Phase 3.2 — Vector Database Configuration & Initialization.

Manages local Chroma DB PersistentClient connections and collections.
(Forwarding import for backward compatibility)
"""

from src.retrieval.phase_3_2_store.store import MFVectorStore

__all__ = ["MFVectorStore"]
