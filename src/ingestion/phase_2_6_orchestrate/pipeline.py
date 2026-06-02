"""Phase 2.6 — Orchestrate subphases 2.1–2.5 with change detection."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from src.corpus.inventory import CorpusEntry, allowed_url_set, load_inventory
from src.ingestion.phase_2_1_fetch.fetcher import fetch_entry, raw_meta_path
from src.ingestion.phase_2_2_parse.parser import parse_entry, parsed_json_path
from src.ingestion.shared.http_client import create_session
from src.ingestion.phase_2_3_normalize.normalizer import normalize_entry, normalized_json_path
from src.ingestion.phase_2_4_chunk.chunker import chunk_all, chunk_entry
from src.ingestion.phase_2_5_store.store import persist_chunks
from src.ingestion.shared.paths import (
    INGEST_MANIFEST_PATH,
    NORMALIZED_DIR,
    PARSED_DIR,
    RAW_DIR,
)

__all__ = [
    "run_ingest",
    "validate_phase2_6",
]

logger = logging.getLogger("ingest_pipeline")


def load_ingest_manifest() -> dict[str, Any]:
    """Load the current ingestion manifest or return a new one if missing."""
    if INGEST_MANIFEST_PATH.is_file():
        try:
            with INGEST_MANIFEST_PATH.open(encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to load manifest: {e}. Starting fresh.")
    return {"version": "1.0", "entries": {}}


def save_ingest_manifest(manifest: dict[str, Any]) -> None:
    """Save the ingestion manifest with pretty formatting and stable key ordering."""
    INGEST_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    # Sort entries by URL for clean diffs
    if "entries" in manifest:
        manifest["entries"] = {k: manifest["entries"][k] for k in sorted(manifest["entries"].keys())}
    with INGEST_MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")


def run_ingest(
    *,
    force: bool = False,
    skip_fetch: bool = False,
    dry_run: bool = False,
    target_id: int | None = None,
) -> int:
    """Orchestrate fetch, parse, normalize, change detection, chunking, and persistence."""
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("  %(levelname)s: %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    print("Phase 2.6 — Running Pipeline Ingestion & Change Detection\n")

    entries = load_inventory()
    if target_id is not None:
        entries = [e for e in entries if e.id == target_id]
        if not entries:
            logger.error(f"No corpus entry found with ID: {target_id}")
            return 1

    manifest = load_ingest_manifest()
    manifest_entries = manifest.get("entries", {})

    allowed = allowed_url_set(entries)
    session = create_session()

    all_chunks: list[dict[str, Any]] = []
    stats = {"fetched": 0, "parsed": 0, "normalized": 0, "skipped": 0, "updated": 0, "failed": 0}

    for entry in sorted(entries, key=lambda e: e.id):
        logger.info(f"Processing ID {entry.id}: {entry.scheme_name or entry.url}")

        try:
            # 1. Fetch
            if skip_fetch:
                # Assert cached HTML exists
                meta_path = raw_meta_path(entry, RAW_DIR)
                if not meta_path.is_file():
                    raise FileNotFoundError(f"skip_fetch=True but missing raw meta sidecar: {meta_path}")
                # Load metadata
                with meta_path.open(encoding="utf-8") as f:
                    meta_payload = json.load(f)
                last_fetched_at = meta_payload["last_fetched_at"]
                logger.info(f"  Fetch skipped. Reusing cached raw files (fetched at {last_fetched_at}).")
            else:
                # Live fetch
                result = fetch_entry(entry, session, allowed, raw_dir=RAW_DIR, force=force)
                stats["fetched"] += 1
                if result.fetch_status not in ("ok", "skipped"):
                    raise ValueError(f"Fetch failed with status {result.fetch_status}: {result.errors}")
                last_fetched_at = result.last_fetched_at
                logger.info(f"  Successfully fetched raw HTML.")

            # 2. Parse
            parsed_doc, parse_res = parse_entry(entry, raw_dir=RAW_DIR, parsed_dir=PARSED_DIR, force=force)
            if parse_res.parse_status == "failed":
                raise ValueError(f"Parse failed: {parse_res.errors}")
            stats["parsed"] += 1
            if parsed_doc is None:
                p_path = parsed_json_path(entry, PARSED_DIR)
                with p_path.open(encoding="utf-8") as f:
                    parsed_payload = json.load(f)
                document_title = parsed_payload.get("document_title") or entry.scheme_name
            else:
                document_title = parsed_doc.document_title or entry.scheme_name

            # 3. Normalize
            norm_doc, norm_res = normalize_entry(entry, parsed_dir=PARSED_DIR, normalized_dir=NORMALIZED_DIR, force=force)
            if norm_res.normalize_status == "failed":
                raise ValueError(f"Normalize failed: {norm_res.errors}")
            stats["normalized"] += 1
            
            if norm_doc is None:
                n_path = normalized_json_path(entry, NORMALIZED_DIR)
                with n_path.open(encoding="utf-8") as f:
                    norm_payload = json.load(f)
                normalized_text = norm_payload["normalized_text"]
                content_hash = norm_payload["content_hash"]
            else:
                normalized_text = norm_doc.normalized_text
                content_hash = norm_doc.content_hash

            # 4. Change Detection Check
            manifest_key = entry.url
            existing = manifest_entries.get(manifest_key)
            is_changed = True

            if existing and not force:
                if existing.get("content_hash") == content_hash:
                    is_changed = False

            if not is_changed:
                logger.info("  Content hash is UNCHANGED. Skipping chunk and manifest updates.")
                stats["skipped"] += 1
                # Re-use metadata dates from the manifest for stable RAG footer dates
                last_fetched_at = existing["last_fetched_at"]
            else:
                logger.info("  Content hash is NEW/CHANGED. Updating manifest.")
                stats["updated"] += 1
                if not dry_run:
                    manifest_entries[manifest_key] = {
                        "content_hash": content_hash,
                        "last_fetched_at": last_fetched_at,
                    }

            # 5. Chunk (In-Memory)
            chunks = chunk_entry(
                entry=entry,
                normalized_text=normalized_text,
                document_title=document_title,
                last_fetched_at=last_fetched_at,
                content_hash=content_hash,
            )
            all_chunks.extend(chunks)
            logger.info(f"  Generated {len(chunks)} chunks.")

        except Exception as e:
            logger.error(f"  Failed processing ID {entry.id}: {e}")
            stats["failed"] += 1
            # If target_id is set, fail immediately. Otherwise, continue to let other docs process.
            if target_id is not None:
                return 1

    # Print summary
    print("\nIngestion Pipeline Summary:")
    print(f"  Total processed: {len(entries)}")
    print(f"  Fetched:         {stats['fetched']}")
    print(f"  Parsed:          {stats['parsed']}")
    print(f"  Normalized:      {stats['normalized']}")
    print(f"  Skipped (hash):  {stats['skipped']}")
    print(f"  Updated/Forced:  {stats['updated']}")
    print(f"  Failed:          {stats['failed']}")

    if stats["failed"] > 0:
        logger.error(f"{stats['failed']} document(s) failed ingestion.")
        return 1

    # 6. Persistence (Skip if dry run)
    if dry_run:
        print(f"\n[Dry Run] Would persist {len(all_chunks)} chunks to store.")
    else:
        # Load all chunks for the entire corpus to rewrite the append-only store
        # Wait, if we processed a subset (target_id was set), we should load the other unchanged chunks
        # from the existing store to make sure we don't lose them, OR if target_id is set we re-compile
        # the store. But to make things extremely robust, if target_id is specified, we can load the chunks for the
        # other 29 pages from the current chunk store, OR we can just regenerate chunks for all 30 pages in-memory
        # (which is extremely fast and takes <10ms!).
        # Yes! Let's just generate all chunks in-memory for the 30 pages to guarantee a 100% complete chunk store.
        if target_id is not None:
            print("\nUpdating the full chunk store with the target ID update...")
            # We already ran chunker on target ID. Let's rebuild the rest from normalized cache.
            # We can simply run `chunk_all()` to rebuild everything correctly using updated files!
            all_chunks = chunk_all()

        persist_chunks(all_chunks)
        manifest["entries"] = manifest_entries
        save_ingest_manifest(manifest)
        print(f"\nSuccessfully persisted {len(all_chunks)} chunks to chunk store.")

    return 0


def validate_phase2_6() -> tuple[bool, list[str]]:
    """Validate Phase 2.6 exit criteria."""
    errors: list[str] = []

    if not INGEST_MANIFEST_PATH.is_file():
        errors.append(f"Missing ingestion manifest at: {INGEST_MANIFEST_PATH}")
        return False, errors

    try:
        with INGEST_MANIFEST_PATH.open(encoding="utf-8") as f:
            manifest = json.load(f)
    except Exception as e:
        return False, [f"Failed to parse manifest: {e}"]

    entries = load_inventory()
    allowed_urls = {e.url for e in entries}

    manifest_entries = manifest.get("entries", {})
    if len(manifest_entries) != len(allowed_urls):
        errors.append(f"Expected {len(allowed_urls)} entries in manifest, found {len(manifest_entries)}")

    for url in allowed_urls:
        if url not in manifest_entries:
            errors.append(f"URL missing from manifest: {url}")
        else:
            entry_data = manifest_entries[url]
            if not entry_data.get("content_hash"):
                errors.append(f"Manifest entry for {url} missing content_hash")
            if not entry_data.get("last_fetched_at"):
                errors.append(f"Manifest entry for {url} missing last_fetched_at")

    return len(errors) == 0, errors
