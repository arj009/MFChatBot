#!/usr/bin/env python3
"""Validate Phase 2.5 exit criteria."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_5_store.store import validate_phase2_5  # noqa: E402
from src.ingestion.shared.paths import CHUNK_STORE_PATH  # noqa: E402


def main() -> int:
    print("Phase 2.5 validation\n")

    if not CHUNK_STORE_PATH.is_file():
        print(f"  - Chunk store file missing at: {CHUNK_STORE_PATH}")
        return 1

    try:
        ok, errors = validate_phase2_5()
        if ok:
            print("  All Phase 2.5 checks passed.")
            return 0

        for err in errors:
            print(f"  - {err}")
        return 1
    except Exception as e:
        print(f"  - Validation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
