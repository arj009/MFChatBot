#!/usr/bin/env python3
"""Phase 2.2 — Parse raw HTML to data/parsed/{id}.json."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_2_parse import parse_all, validate_phase2_2  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2.2 HTML parse")
    parser.add_argument("--force", action="store_true", help="Re-parse all files")
    args = parser.parse_args()

    print("Phase 2.2 — HTML parse\n")
    results, manifest = parse_all(force=args.force)

    ok = sum(1 for r in results if r.parse_status == "ok")
    skipped = sum(1 for r in results if r.parse_status == "skipped")
    failed = sum(1 for r in results if r.parse_status == "failed")
    print(f"  Manifest: {manifest}")
    print(f"  OK: {ok}  Skipped: {skipped}  Failed: {failed}")

    for r in results:
        if r.parse_status != "ok":
            print(f"    [{r.parse_status.upper()}] #{r.entry_id}")
            for err in r.errors:
                print(f"          {err}")

    valid, errors = validate_phase2_2()
    if valid:
        print("\nPhase 2.2 exit criteria: all satisfied.")
        return 0 if failed == 0 else 1

    print("\nPhase 2.2 exit criteria: not satisfied.")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
