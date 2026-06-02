"""Load and validate the closed 30-URL Groww corpus (Phase 0)."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse, urlunparse

import yaml

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CORPUS_DIR = PROJECT_ROOT / "corpus"
SCOPE_PATH = CORPUS_DIR / "scope.yaml"
INVENTORY_CSV_PATH = CORPUS_DIR / "url_inventory.csv"
SOURCES_JSON_PATH = CORPUS_DIR / "sources.json"

EXPECTED_URL_COUNT = 30
AMC_NAME = "ICICI Prudential Mutual Fund"
ALLOWED_SOURCE_TYPES = frozenset({"scheme_page", "amc_listing"})


@dataclass(frozen=True)
class CorpusEntry:
    id: int
    scheme_name: str
    category: str
    url: str
    scheme_slug: str | None
    source_type: str
    status: str
    last_reviewed: str


def normalize_url(url: str) -> str:
    """Canonical form for closed-corpus matching (Phase 2 ingestion guard)."""
    parsed = urlparse(url.strip())
    scheme = parsed.scheme.lower() or "https"
    netloc = parsed.netloc.lower()
    path = parsed.path.rstrip("/")
    # Preserve query string exactly for filter listing (#9)
    normalized = urlunparse((scheme, netloc, path, "", parsed.query, ""))
    return normalized


def _repo_path(path: Path | None) -> Path:
    return path if path is not None else INVENTORY_CSV_PATH


def load_scope(path: Path | None = None) -> dict[str, Any]:
    scope_path = path or SCOPE_PATH
    with scope_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def load_inventory(csv_path: Path | None = None) -> list[CorpusEntry]:
    path = _repo_path(csv_path)
    entries: list[CorpusEntry] = []
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            raw_id = row.get("id", "").strip()
            if not raw_id:
                continue
            slug = (row.get("scheme_slug") or "").strip() or None
            entries.append(
                CorpusEntry(
                    id=int(raw_id),
                    scheme_name=row["scheme_name"].strip(),
                    category=row["category"].strip(),
                    url=row["url"].strip(),
                    scheme_slug=slug,
                    source_type=row["source_type"].strip(),
                    status=row["status"].strip(),
                    last_reviewed=(row.get("last_reviewed") or "").strip(),
                )
            )
    return entries


def allowed_url_set(entries: list[CorpusEntry] | None = None) -> frozenset[str]:
    items = entries if entries is not None else load_inventory()
    return frozenset(normalize_url(e.url) for e in items)


def is_allowed_url(url: str, entries: list[CorpusEntry] | None = None) -> bool:
    return normalize_url(url) in allowed_url_set(entries)


class ClosedCorpusError(ValueError):
    """Raised when a URL is not in the closed 30-URL inventory."""


def enforce_closed_url(url: str, entries: list[CorpusEntry] | None = None) -> str:
    """Phase 1 closed-list enforcer — returns normalized URL or raises."""
    normalized = normalize_url(url)
    if not is_allowed_url(url, entries):
        raise ClosedCorpusError(f"URL not in closed corpus: {url}")
    return normalized


def validate_inventory(entries: list[CorpusEntry] | None = None) -> list[str]:
    """Return list of validation errors (empty if valid)."""
    items = entries if entries is not None else load_inventory()
    errors: list[str] = []

    if len(items) != EXPECTED_URL_COUNT:
        errors.append(f"Expected {EXPECTED_URL_COUNT} URLs, got {len(items)}")

    ids = [e.id for e in items]
    if len(ids) != len(set(ids)):
        errors.append("Duplicate id values in inventory")

    urls = [normalize_url(e.url) for e in items]
    if len(urls) != len(set(urls)):
        errors.append("Duplicate normalized URLs in inventory")

    scheme_pages = [e for e in items if e.source_type == "scheme_page"]
    listings = [e for e in items if e.source_type == "amc_listing"]
    if len(scheme_pages) != 29:
        errors.append(f"Expected 29 scheme_page rows, got {len(scheme_pages)}")
    if len(listings) != 1:
        errors.append(f"Expected 1 amc_listing row, got {len(listings)}")

    for e in items:
        if e.status != "approved":
            errors.append(f"Row {e.id}: status must be 'approved', got '{e.status}'")
        if e.source_type not in ALLOWED_SOURCE_TYPES:
            errors.append(f"Row {e.id}: invalid source_type '{e.source_type}'")
        parsed = urlparse(e.url)
        if parsed.netloc.lower() not in ("groww.in", "www.groww.in"):
            errors.append(f"Row {e.id}: URL must be on groww.in")
        if e.source_type == "scheme_page" and not e.scheme_slug:
            errors.append(f"Row {e.id}: scheme_page missing scheme_slug")
        if e.source_type == "amc_listing" and e.scheme_slug:
            errors.append(f"Row {e.id}: amc_listing must not have scheme_slug")
        if e.source_type == "scheme_page" and e.scheme_slug:
            if e.scheme_slug not in parsed.path:
                errors.append(f"Row {e.id}: URL path does not contain scheme_slug")

    return errors


def sync_sources_json() -> Path:
    errors = validate_inventory()
    if errors:
        raise ValueError("Inventory invalid:\n" + "\n".join(f"  - {e}" for e in errors))
    return export_sources_json()


def save_inventory(rows: list[dict[str, str]], csv_path: Path | None = None) -> Path:
    """Write url_inventory.csv from row dicts (Phase 1 curation updates)."""
    path = csv_path or INVENTORY_CSV_PATH
    fieldnames = [
        "id",
        "scheme_name",
        "category",
        "url",
        "scheme_slug",
        "source_type",
        "status",
        "last_reviewed",
    ]
    sorted_rows = sorted(rows, key=lambda r: int(r["id"]))
    if len(sorted_rows) != EXPECTED_URL_COUNT:
        raise ValueError(f"Refusing to save: expected {EXPECTED_URL_COUNT} rows, got {len(sorted_rows)}")

    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in sorted_rows:
            writer.writerow({k: row.get(k, "") for k in fieldnames})
        f.write("\n")
    return path


def export_sources_json(
    entries: list[CorpusEntry] | None = None,
    output_path: Path | None = None,
) -> Path:
    items = entries if entries is not None else load_inventory()
    out = output_path or SOURCES_JSON_PATH
    payload = {
        "version": "1.0",
        "amc": AMC_NAME,
        "corpus_policy": "closed",
        "url_count": len(items),
        "sources": [
            {
                "id": e.id,
                "scheme_name": e.scheme_name if e.source_type == "scheme_page" else None,
                "category": e.category,
                "url": e.url,
                "url_normalized": normalize_url(e.url),
                "scheme_slug": e.scheme_slug,
                "source_type": e.source_type,
                "status": e.status,
                "last_reviewed": e.last_reviewed or None,
            }
            for e in sorted(items, key=lambda x: x.id)
        ],
    }
    with out.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")
    return out
