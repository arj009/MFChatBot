#!/usr/bin/env python3
"""Phase 1 — Validate closed corpus URLs (reachability + content checks)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.curation import (  # noqa: E402
    CURATION_REPORT_PATH,
    load_curation_report,
    phase1_exit_ok,
    run_curation,
)
from src.corpus.inventory import load_inventory, validate_inventory  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 1 corpus curation")
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Seconds between HTTP requests (default: 1.0)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run checks but do not update url_inventory.csv",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Validate using existing curation_report.json only (no network)",
    )
    parser.add_argument(
        "--ids",
        type=str,
        default="",
        help="Comma-separated inventory ids to check (default: all 30)",
    )
    args = parser.parse_args()

    print("Phase 1 — Corpus curation\n")

    structural = validate_inventory()
    if structural:
        print("Inventory structure invalid:")
        for err in structural:
            print(f"  - {err}")
        return 1
    print("  Inventory structure: OK (30 URLs)")

    if args.offline:
        report_data = load_curation_report()
        if not report_data:
            print("  No curation report found. Run without --offline first.")
            return 1
        ok, errors = phase1_exit_ok()
        if ok:
            print("  Offline Phase 1 exit: OK")
            return 0
        for err in errors:
            print(f"  - {err}")
        return 1

    entries = load_inventory()
    partial = False
    if args.ids.strip():
        wanted = {int(x.strip()) for x in args.ids.split(",")}
        entries = [e for e in entries if e.id in wanted]
        partial = True
        if not entries:
            print("  No matching inventory ids.")
            return 1

    update_inv = not args.dry_run and not partial
    if partial and not args.dry_run:
        print("  Partial id run — inventory will not be updated (use full run).")

    report = run_curation(
        request_delay=args.delay,
        update_inventory=update_inv,
        entries=entries,
    )

    print(f"\n  Report: {CURATION_REPORT_PATH}")
    print(f"  Passed: {report.passed_count}/{report.url_count}")
    print(f"  Failed: {report.failed_count}/{report.url_count}")

    for result in report.results:
        status = "OK" if result.passed else "FAIL"
        gaps = f" gaps={result.content_gaps}" if result.content_gaps else ""
        print(f"    [{status}] #{result.entry_id} HTTP {result.http_status}{gaps}")
        if not result.passed:
            for err in result.errors:
                print(f"          {err}")

    ok, errors = phase1_exit_ok(report if not args.dry_run else None)
    if args.dry_run:
        print("\n  Dry run — inventory not updated.")
        return 0 if report.failed_count == 0 else 1

    if ok:
        print("\nPhase 1 exit criteria: all satisfied.")
        return 0

    print("\nPhase 1 exit criteria: not satisfied.")
    for err in errors:
        print(f"  - {err}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
