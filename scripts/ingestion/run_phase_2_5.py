#!/usr/bin/env python3
"""Phase 2.5 — Persist chunks to data/chunks/chunk_store.jsonl."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_4_chunk.chunker import chunk_all  # noqa: E402
from src.ingestion.phase_2_5_store.store import persist_chunks, validate_phase2_5  # noqa: E402
from src.ingestion.shared.paths import CHUNK_STORE_PATH  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2.5 runner")
    parser.parse_args()

    print("Phase 2.5 — Persist Chunk Store\n")

    try:
        # 1. Generate the chunks
        chunks = chunk_all()
        print(f"  Generated {len(chunks)} chunks in-memory.")

        # 2. Persist the chunks
        persist_chunks(chunks)
        print(f"  Successfully wrote chunks to: {CHUNK_STORE_PATH}")

        # Get file size
        file_size_kb = CHUNK_STORE_PATH.stat().st_size / 1024
        print(f"  Chunk store size: {file_size_kb:.2f} KB")

        # 3. Run validation
        valid, errors = validate_phase2_5()
        if valid:
            print("\nPhase 2.5 exit criteria: all satisfied.")
            return 0

        print("\nPhase 2.5 exit criteria: not satisfied.")
        for err in errors:
            print(f"  - {err}")
        return 1

    except Exception as e:
        print(f"  Error running Phase 2.5 persistence: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
