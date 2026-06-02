"""Data paths for Phase 2 ingestion subphases."""

from pathlib import Path

from src.corpus.inventory import PROJECT_ROOT

RAW_DIR = PROJECT_ROOT / "data" / "raw"
PARSED_DIR = PROJECT_ROOT / "data" / "parsed"
NORMALIZED_DIR = PROJECT_ROOT / "data" / "normalized"
CHUNKS_DIR = PROJECT_ROOT / "data" / "chunks"
CHUNK_STORE_PATH = CHUNKS_DIR / "chunk_store.jsonl"
INGEST_MANIFEST_PATH = PROJECT_ROOT / "corpus" / "ingest_manifest.json"

FETCH_MANIFEST_PATH = RAW_DIR / "fetch_manifest.json"
PARSE_MANIFEST_PATH = PARSED_DIR / "parse_manifest.json"
NORMALIZE_MANIFEST_PATH = NORMALIZED_DIR / "normalize_manifest.json"
