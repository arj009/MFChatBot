#!/usr/bin/env python3
"""Validate Phase 0 exit criteria (closed corpus, inventory, sources.json)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import (  # noqa: E402
    EXPECTED_URL_COUNT,
    SOURCES_JSON_PATH,
    load_inventory,
    load_scope,
    normalize_url,
    sync_sources_json,
    validate_inventory,
)


def main() -> int:
    print("Phase 0 validation — MFChatBot closed corpus\n")

    scope = load_scope()
    assert scope["corpus_policy"] == "closed"
    assert scope["url_count"] == EXPECTED_URL_COUNT
    print(f"  scope.yaml: OK (AMC={scope['amc']}, urls={scope['url_count']})")

    entries = load_inventory()
    errors = validate_inventory(entries)
    if errors:
        print("  url_inventory.csv: FAILED")
        for err in errors:
            print(f"    - {err}")
        return 1
    print(f"  url_inventory.csv: OK ({len(entries)} approved URLs)")

    sync_sources_json()
    with SOURCES_JSON_PATH.open(encoding="utf-8") as f:
        sources = json.load(f)
    json_urls = {s["url_normalized"] for s in sources["sources"]}
    csv_urls = {normalize_url(e.url) for e in entries}
    if json_urls != csv_urls:
        print("  sources.json: FAILED (out of sync with CSV)")
        return 1
    print(f"  sources.json: OK (synced, {sources['url_count']} sources)")

    print("\nPhase 0 exit criteria:")
    print("  [x] AMC and URL inventory fixed")
    print("  [x] Closed corpus — exactly 30 URLs")
    print("  [x] url_inventory.csv generated")
    print("  [x] Refusal categories — docs/compliance-rules.md")
    print("  [x] Golden queries — tests/golden/golden_queries.yaml")
    print("\nAll Phase 0 checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
