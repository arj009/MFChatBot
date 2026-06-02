#!/usr/bin/env python3
"""Validate Phase 2.6 exit criteria."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_6_orchestrate.pipeline import validate_phase2_6  # noqa: E402
from src.ingestion.shared.paths import INGEST_MANIFEST_PATH  # noqa: E402


def main() -> int:
    print("Phase 2.6 validation\n")

    if not INGEST_MANIFEST_PATH.is_file():
        print(f"  - Ingestion manifest missing at: {INGEST_MANIFEST_PATH}")
        return 1

    try:
        ok, errors = validate_phase2_6()
        if ok:
            print("  All Phase 2.6 checks passed.")
            return 0

        for err in errors:
            print(f"  - {err}")
        return 1
    except Exception as e:
        print(f"  - Validation error: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
