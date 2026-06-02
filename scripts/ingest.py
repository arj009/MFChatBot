#!/usr/bin/env python3
"""Orchestrate Phase 2 ingestion pipeline: fetch, parse, normalize, chunk, and persist."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_6_orchestrate.pipeline import run_ingest, validate_phase2_6  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="MFChatBot Closed Corpus Ingest Pipeline")
    parser.add_argument(
        "--id",
        type=int,
        help="Process a single document by its inventory ID (1-30)",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore change detection and force update all processed documents",
    )
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Do not query groww.in; reuse locally cached raw HTML files",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Execute pipeline stages but do not write ingest manifest or chunk store",
    )

    args = parser.parse_args()

    # Execute ingestion
    status = run_ingest(
        force=args.force,
        skip_fetch=args.skip_fetch,
        dry_run=args.dry_run,
        target_id=args.id,
    )

    if status == 0 and not args.dry_run:
        # Run validation
        print("\nRunning post-ingest Phase 2.6 validations...")
        ok, errors = validate_phase2_6()
        if ok:
            print("  [x] Ingest manifest matches 30 approved URLs")
            print("  [x] All Phase 2.6 exit criteria satisfied successfully.")
            return 0
        else:
            print("  [-] Phase 2.6 validation FAILED:")
            for err in errors:
                print(f"    - {err}")
            return 1

    return status


if __name__ == "__main__":
    sys.exit(main())
