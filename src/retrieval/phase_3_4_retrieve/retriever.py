"""Phase 3.4 — Basic Semantic Retriever API.

Exposes core Top-k vector nearest-neighbor retrieval over persistent mutual fund chunks.
"""

from __future__ import annotations

import logging
import pathlib
from typing import Any

from src.retrieval.phase_3_1_embed.embedder import MFEmbedder
from src.retrieval.phase_3_2_store.store import MFVectorStore
from src.retrieval.phase_3_5_filter.filter import find_matching_slugs
from src.retrieval.phase_3_6_deduplicate.deduplicator import deduplicate_chunks

__all__ = ["MFRetriever", "retrieve"]

logger = logging.getLogger("retrieval.retriever")

DEFAULT_INDEX_DIR = pathlib.Path("data/index")


class MFRetriever:
    """Core Top-k nearest-neighbor semantic retriever over persistent mutual fund chunks."""

    def __init__(self, index_dir: pathlib.Path | str = DEFAULT_INDEX_DIR) -> None:
        """Initialize the retriever with a persistent Chroma index path."""
        self.index_dir = pathlib.Path(index_dir).resolve()
        logger.info(f"Initializing MFRetriever with index at '{self.index_dir}'...")

    def retrieve(
        self,
        query: str,
        top_k: int = 3,
        scheme_hint: str | None = None,
        deduplicate: bool = True,
    ) -> list[dict[str, Any]]:
        """Perform a top-k semantic search query with optional scheme filtering and deduplication.

        Args:
            query: The user search query string.
            top_k: The number of top semantically matching chunks to return.
            scheme_hint: An optional string to filter matching chunks to specific mutual fund schemes.
                         Can be a partial/exact scheme name or a scheme slug.
            deduplicate: If True, returns at most one chunk (the highest-scoring) per unique source_url.

        Returns:
            A list of dictionary items, each containing:
                - "id": The unique chunk identifier in Chroma.
                - "text": The plain text content of the chunk.
                - "metadata": The 10 schema metadata fields.
                - "score": The calculated similarity score (Cosine Similarity: 1.0 - Cosine Distance).
        """
        query_str = query.strip()
        if not query_str:
            logger.warning("Empty query received. Returning empty list.")
            return []

        # 1. Get embedding for the query string using Phase 3.1 Embedder
        query_embedding = MFEmbedder.embed_text(query_str)

        # 2. Access the Chroma store using Phase 3.2 Store manager
        collection = MFVectorStore.get_collection(self.index_dir)
        total_records = collection.count()
        if total_records == 0:
            logger.warning("Chroma collection is empty. Returning empty list.")
            return []

        # 3. Build dynamic metadata filter using Phase 3.5 filtering
        where_filter = None
        matching_slugs = []
        if scheme_hint:
            matching_slugs = find_matching_slugs(scheme_hint)
            if len(matching_slugs) == 1:
                where_filter = {"scheme_slug": matching_slugs[0]}
                logger.info(f"Applying exact scheme slug filter: '{matching_slugs[0]}'")
            elif len(matching_slugs) > 1:
                where_filter = {"scheme_slug": {"$in": matching_slugs}}
                logger.info(f"Applying multiple scheme slugs filter: {matching_slugs}")
            else:
                # If no specific slugs matched, do not apply a metadata filter
                # and let semantic search rank across the entire database.
                where_filter = None
                logger.info(f"No exact scheme slugs resolved for hint '{scheme_hint}'. Proceeding with unrestricted search.")

        # 4. Query closest top_k vector neighbors
        # If deduplicating, we need to fetch more chunks internally because multiple
        # top hits can belong to the same source_url.
        fetch_k = max(top_k * 3, 20) if deduplicate else top_k
        n_results = min(fetch_k, total_records)

        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where_filter,
        )

        # 5. If schemes were matched, always fetch and inject key facts chunks (chunk_index 0)
        # to ensure factual data like NAV, expense ratio, etc. is always available
        logger.info(f"matching_slugs: {matching_slugs}")
        key_facts_items = []
        if matching_slugs:
            for slug in matching_slugs:
                logger.info(f"Attempting to inject key facts chunk for scheme: '{slug}'")
                key_facts_filter = {"$and": [{"scheme_slug": slug}, {"chunk_index": 0}]}
                key_facts_results = collection.query(
                    query_embeddings=[query_embedding],
                    n_results=1,
                    where=key_facts_filter,
                )
                logger.info(f"Key facts query results: {key_facts_results.get('ids', [])}")
                if key_facts_results and key_facts_results.get("documents") and key_facts_results["documents"][0]:
                    # Extract key facts chunk
                    key_facts_id = key_facts_results["ids"][0][0]
                    key_facts_doc = key_facts_results["documents"][0][0]
                    key_facts_meta = key_facts_results["metadatas"][0][0]
                    key_facts_dist = key_facts_results.get("distances", [[]])[0][0] if key_facts_results.get("distances") else 0.0
                    
                    # Store key facts chunk separately to add after deduplication
                    key_facts_items.append({
                        "id": key_facts_id,
                        "text": key_facts_doc,
                        "metadata": key_facts_meta,
                        "score": float(1.0 - key_facts_dist),
                    })
                    logger.info(f"Stored key facts chunk for scheme '{slug}'")

        raw_items: list[dict[str, Any]] = []
        if not results or not results.get("documents"):
            return raw_items

        # Unpack Chroma lists (single-query format, i.e., index 0)
        ids = results["ids"][0]
        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results.get("distances", [[]])[0]

        for i in range(len(ids)):
            # Convert Cosine Distance (computed by Chroma) to Cosine Similarity score
            distance = distances[i] if i < len(distances) else 0.0
            similarity_score = float(1.0 - distance)

            raw_items.append({
                "id": ids[i],
                "text": documents[i],
                "metadata": metadatas[i],
                "score": similarity_score,
            })

        # 5. Apply single citation URL deduplication using Phase 3.6 deduplicator
        if deduplicate:
            retrieved_items = deduplicate_chunks(raw_items, top_k)
        else:
            retrieved_items = raw_items[:top_k]

        # 6. Inject key facts chunks at the beginning of results (bypass deduplication)
        # This ensures factual data like NAV is always available even if it has lower semantic score
        if key_facts_items:
            # Remove any existing chunks from the same scheme to avoid duplicates
            scheme_urls = {item["metadata"]["source_url"] for item in key_facts_items}
            retrieved_items = [item for item in retrieved_items if item["metadata"]["source_url"] not in scheme_urls]
            
            # Add key facts chunks at the beginning
            retrieved_items = key_facts_items + retrieved_items
            
            # Trim to top_k
            retrieved_items = retrieved_items[:top_k]
            logger.info(f"Injected {len(key_facts_items)} key facts chunks into final results")

        logger.debug(f"Retrieved {len(retrieved_items)} items (dedup={deduplicate}) for query: '{query_str}'")
        return retrieved_items


def retrieve(
    query: str,
    top_k: int = 3,
    scheme_hint: str | None = None,
    deduplicate: bool = True,
    index_dir: pathlib.Path | str = DEFAULT_INDEX_DIR,
) -> list[dict[str, Any]]:
    """Standard package-level utility function for top-k semantic retrieval with filtering and deduplication."""
    retriever = MFRetriever(index_dir=index_dir)
    return retriever.retrieve(
        query=query,
        top_k=top_k,
        scheme_hint=scheme_hint,
        deduplicate=deduplicate,
    )
