"""Phase 3.3 — Index Builder core logic.

Reads JSONL chunk store, vectorizes text sections locally, and populates Chroma DB.
"""

from __future__ import annotations

import json
import logging
import pathlib
from typing import Any

from src.retrieval.phase_3_1_embed.embedder import MFEmbedder
from src.retrieval.phase_3_2_store.store import MFVectorStore

logger = logging.getLogger("retrieval.build_index")


def build_index(
    store_path: pathlib.Path | str,
    index_dir: pathlib.Path | str,
    dry_run: bool = False,
) -> int:
    """Build the persistent Chroma vector index from chunk store JSONL file.

    Returns:
        0 on success, non-zero on failure.
    """
    store_file = pathlib.Path(store_path).resolve()
    db_dir = pathlib.Path(index_dir).resolve()

    logger.info(f"Starting index builder...")
    logger.info(f"Input chunk store: '{store_file}'")
    logger.info(f"Output vector DB:  '{db_dir}'")
    if dry_run:
        logger.info("NOTE: Running in DRY-RUN mode. No database writes will occur.")

    if not store_file.is_file():
        logger.error(f"Chunk store file does not exist: {store_file}. Run ingestion pipeline first.")
        return 1

    # 1. Load chunks from chunk store
    logger.info("Reading chunks from store...")
    chunks: list[dict[str, Any]] = []
    try:
        with store_file.open(encoding="utf-8") as f:
            for line_idx, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = json.loads(line)
                    chunks.append(chunk)
                except json.JSONDecodeError as e:
                    logger.error(f"Malformed JSON on line {line_idx}: {e}")
                    return 1
    except Exception as e:
        logger.error(f"Failed to read chunk store: {e}")
        return 1

    total_chunks = len(chunks)
    logger.info(f"Successfully loaded {total_chunks} chunks.")
    if total_chunks == 0:
        logger.warning("No chunks to index.")
        return 0

    # 2. Extract texts and prepare clean metadata fields
    texts: list[str] = []
    metadatas: list[dict[str, str | int | float | bool]] = []
    ids: list[str] = []

    for idx, chunk in enumerate(chunks):
        # Extract text content
        text = chunk.get("text", "").strip()
        if not text:
            logger.warning(f"Empty text found in chunk {idx}. Skipping.")
            continue
        texts.append(text)

        # Build clean metadata: replace None values with "" to comply with Chroma's restrictions
        meta: dict[str, str | int | float | bool] = {}
        for key in [
            "source_url",
            "source_type",
            "amc",
            "scheme_name",
            "scheme_slug",
            "scheme_category",
            "document_title",
            "last_fetched_at",
            "content_hash",
            "chunk_index",
        ]:
            val = chunk.get(key)
            if val is None:
                meta[key] = ""
            else:
                meta[key] = val
        metadatas.append(meta)

        # Generate unique chunk ID
        slug = chunk.get("scheme_slug") or "amc_list"
        chunk_idx = chunk.get("chunk_index", 0)
        ids.append(f"c_{idx:03d}_{slug}_ch{chunk_idx}")

    # 3. Generate embeddings using MFEmbedder
    logger.info("Generating semantic embeddings...")
    try:
        # MFEmbedder.embed_texts handles batched processing (batch size = 64) with CPU optimization
        embeddings = MFEmbedder.embed_texts(texts, show_progress=True)
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        return 1

    logger.info(f"Generated {len(embeddings)} normalized embeddings.")

    # 4. Populate Chroma DB (unless dry run)
    if dry_run:
        logger.info(f"[Dry Run] Would have index rebuilt with {len(ids)} segments.")
        return 0

    try:
        # Recreate the collection (wipe legacy data for reproducibility)
        MFVectorStore.reset_store(db_dir)
        collection = MFVectorStore.get_collection(db_dir)

        # Batch writes to Chroma DB
        logger.info("Writing embeddings and metadata to Chroma DB...")
        write_batch_size = 100
        for i in range(0, len(ids), write_batch_size):
            end_idx = min(i + write_batch_size, len(ids))
            logger.info(f"Indexing chunks {i} to {end_idx - 1}...")
            collection.add(
                ids=ids[i:end_idx],
                embeddings=embeddings[i:end_idx],
                documents=texts[i:end_idx],
                metadatas=metadatas[i:end_idx],
            )

        logger.info(f"Successfully compiled vector DB with {collection.count()} chunks.")
    except Exception as e:
        logger.error(f"Failed to populate Chroma DB: {e}")
        return 1

    return 0
