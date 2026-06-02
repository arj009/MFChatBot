#!/usr/bin/env python3
"""Phase 2.1 — Fetch and cache raw HTML for the closed 30-URL corpus."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import load_inventory  # noqa: E402
from src.ingestion.phase_2_1_fetch import fetch_all, validate_phase2_1  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2.1 raw HTML fetch")
    parser.add_argument("--delay", type=float, default=1.0, help="Seconds between requests")
    parser.add_argument("--force", action="store_true", help="Re-fetch even if cached")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated inventory ids")
    args = parser.parse_args()

    print("Phase 2.1 — Closed-list fetch & raw cache\n")

    entries = load_inventory()
    if args.ids.strip():
        wanted = {int(x.strip()) for x in args.ids.split(",")}
        entries = [e for e in entries if e.id in wanted]

    results, manifest_path = fetch_all(
        entries=entries,
        request_delay=args.delay,
        force=args.force,
    )

    ok = sum(1 for r in results if r.fetch_status == "ok")
    skipped = sum(1 for r in results if r.fetch_status == "skipped")
    failed = sum(1 for r in results if r.fetch_status == "failed")

    print(f"  Manifest: {manifest_path}")
    print(f"  OK: {ok}  Skipped: {skipped}  Failed: {failed}")

    for r in results:
        print(f"    [{r.fetch_status.upper()}] #{r.entry_id} HTTP {r.http_status}")
        for err in r.errors:
            print(f"          {err}")

    if len(entries) == 30:
        valid, errors = validate_phase2_1()
        if valid:
            print("\nPhase 2.1 exit criteria: all satisfied.")
            return 0
        print("\nPhase 2.1 exit criteria: not satisfied.")
        for err in errors:
            print(f"  - {err}")
        return 1

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
