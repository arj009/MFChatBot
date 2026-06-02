#!/usr/bin/env python3
"""Validate Phase 2.2 exit criteria."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import EXPECTED_URL_COUNT, load_inventory  # noqa: E402
from src.ingestion.phase_2_2_parse import parsed_json_path, validate_phase2_2  # noqa: E402
from src.ingestion.shared.paths import PARSED_DIR  # noqa: E402


def main() -> int:
    print("Phase 2.2 validation\n")
    count = sum(1 for e in load_inventory() if parsed_json_path(e, PARSED_DIR).is_file())
    print(f"  Parsed files: {count}/{EXPECTED_URL_COUNT}")
    ok, errors = validate_phase2_2()
    if ok:
        print("\nAll Phase 2.2 checks passed.")
        return 0
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
