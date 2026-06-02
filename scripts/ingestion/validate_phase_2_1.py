#!/usr/bin/env python3
"""Validate Phase 2.1 exit criteria."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import EXPECTED_URL_COUNT, load_inventory  # noqa: E402
from src.ingestion.phase_2_1_fetch import raw_html_path, validate_phase2_1  # noqa: E402
from src.ingestion.shared.paths import RAW_DIR  # noqa: E402


def main() -> int:
    print("Phase 2.1 validation\n")
    entries = load_inventory()
    html_count = sum(1 for e in entries if raw_html_path(e, RAW_DIR).is_file())
    print(f"  HTML files: {html_count}/{EXPECTED_URL_COUNT}")

    ok, errors = validate_phase2_1()
    if ok:
        print("\nAll Phase 2.1 checks passed.")
        return 0
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
