#!/usr/bin/env python3
"""Phase 3.3 — Index Builder CLI.

Reads JSONL chunk store, vectorizes text sections locally, and populates Chroma DB.
"""

from __future__ import annotations

import argparse
import logging
import pathlib
import sys

# Add workspace root to sys.path to enable absolute imports
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.retrieval.phase_3_3_build_index.builder import build_index  # noqa: E402

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("build_index")

DEFAULT_STORE_PATH = ROOT / "data" / "chunks" / "chunk_store.jsonl"
DEFAULT_INDEX_DIR = ROOT / "data" / "index"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Phase 3.3 — Index Builder CLI")
    parser.add_argument(
        "--store-path",
        "-s",
        type=str,
        default=str(DEFAULT_STORE_PATH),
        help="Path to chunk_store.jsonl",
    )
    parser.add_argument(
        "--index-dir",
        "-i",
        type=str,
        default=str(DEFAULT_INDEX_DIR),
        help="Path to persistent Chroma DB index directory",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform a dry-run without writing to database",
    )

    args = parser.parse_args()
    sys.exit(
        build_index(
            store_path=args.store_path,
            index_dir=args.index_dir,
            dry_run=args.dry_run,
        )
    )
