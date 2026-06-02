#!/usr/bin/env python3
"""Regenerate corpus/sources.json from corpus/url_inventory.csv."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import sync_sources_json  # noqa: E402


if __name__ == "__main__":
    path = sync_sources_json()
    print(f"Wrote {path}")
