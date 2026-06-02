#!/usr/bin/env python3
"""Railway startup entrypoint for MFChatBot backend."""

from __future__ import annotations

import logging
import os
import pathlib
import sys

import uvicorn

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.retrieval.phase_3_2_store.store import MFVectorStore  # noqa: E402
from src.retrieval.phase_3_3_build_index.builder import build_index  # noqa: E402

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("railway.start")


def ensure_index() -> None:
    """Build vector index if it does not already contain chunks."""
    store_path = ROOT / "data" / "chunks" / "chunk_store.jsonl"
    index_dir = ROOT / "data" / "index"

    existing_count = 0
    try:
        collection = MFVectorStore.get_collection(index_dir)
        existing_count = collection.count()
    except Exception as exc:  # pragma: no cover - defensive startup guard
        logger.warning(f"Unable to inspect existing index: {exc}")

    if existing_count > 0:
        logger.info(f"Existing vector index detected ({existing_count} chunks).")
        return

    if not store_path.exists():
        logger.warning(f"Chunk store missing at '{store_path}'. Starting API without retrieval index.")
        return

    logger.info("No vector index found. Building index from chunk store for Railway startup...")
    code = build_index(store_path=store_path, index_dir=index_dir, dry_run=False)
    if code != 0:
        raise RuntimeError("Index build failed during Railway startup.")


def main() -> None:
    ensure_index()
    port = int(os.environ.get("PORT", "8000"))
    logger.info(f"Starting API server on 0.0.0.0:{port}")
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
