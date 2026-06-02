"""Phase 3.6 — Deduplication & Context Formatting.

Provides single-citation URL deduplication logic, grouping search hits to avoid multi-citation leaks.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger("retrieval.deduplicator")

__all__ = ["deduplicate_chunks"]


def deduplicate_chunks(raw_items: list[dict[str, Any]], top_k: int) -> list[dict[str, Any]]:
    """Group neighboring semantic matches and retain only the highest-scoring chunk per unique URL.

    Args:
        raw_items: Raw search hit dictionaries containing 'metadata' and 'score'.
        top_k: The final number of items to return after deduplication.

    Returns:
        A list of top_k deduplicated items sorted by score descending.
    """
    seen_urls: dict[str, dict[str, Any]] = {}
    for item in raw_items:
        url = item["metadata"].get("source_url")
        if not url:
            # Fallback to chunk ID as unique key if no URL is provided
            url = item["id"]
        
        # Chroma returns items sorted by similarity score descending.
        # Thus, the first hit for any unique URL is guaranteed to be the highest scoring!
        if url not in seen_urls:
            seen_urls[url] = item

    # Re-sort deduplicated items to be absolutely certain order is correct
    deduplicated_items = list(seen_urls.values())
    deduplicated_items.sort(key=lambda x: x["score"], reverse=True)
    
    return deduplicated_items[:top_k]
