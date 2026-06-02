#!/usr/bin/env python3
"""Validate Phase 2.3 exit criteria."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import EXPECTED_URL_COUNT, load_inventory  # noqa: E402
from src.ingestion.phase_2_3_normalize import normalized_json_path, validate_phase2_3  # noqa: E402
from src.ingestion.shared.paths import NORMALIZED_DIR  # noqa: E402


def main() -> int:
    print("Phase 2.3 validation\n")
    count = sum(
        1 for e in load_inventory() if normalized_json_path(e, NORMALIZED_DIR).is_file()
    )
    print(f"  Normalized files: {count}/{EXPECTED_URL_COUNT}")
    ok, errors = validate_phase2_3()
    if ok:
        print("\nAll Phase 2.3 checks passed.")
        return 0
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
