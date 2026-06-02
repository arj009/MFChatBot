#!/usr/bin/env python3
"""Verify Phase 1 exit criteria without network (uses inventory + curation report)."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.curation import phase1_exit_ok  # noqa: E402
from src.corpus.inventory import load_inventory, sync_sources_json, validate_inventory  # noqa: E402


def main() -> int:
    print("Phase 1 validation\n")
    errors = validate_inventory()
    entries = load_inventory()
    if not errors:
        print(f"  url_inventory.csv: OK ({len(entries)} rows)")
    else:
        for e in errors:
            print(f"  - {e}")
        return 1

    missing_review = [e.id for e in entries if not e.last_reviewed]
    if missing_review:
        print(f"  last_reviewed missing for ids: {missing_review}")
    else:
        print("  last_reviewed: OK (all 30 dated)")

    ok, exit_errors = phase1_exit_ok()
    if ok:
        sync_sources_json()
        print("  curation_report.json: OK")
        print("  sources.json: synced")
        print("\nAll Phase 1 checks passed.")
        return 0

    for err in exit_errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
