#!/usr/bin/env python3
"""Validate Phase 2.4 exit criteria."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_4_chunk.chunker import chunk_all, validate_phase2_4  # noqa: E402


def main() -> int:
    print("Phase 2.4 validation\n")

    try:
        chunks = chunk_all()
        print(f"  Generated chunks: {len(chunks)}")

        ok, errors = validate_phase2_4(chunks)
        if ok:
            print("\nAll Phase 2.4 checks passed.")
            return 0

        for err in errors:
            print(f"  - {err}")
        return 1
    except Exception as e:
        print(f"  - Validation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
