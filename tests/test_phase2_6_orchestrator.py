"""Tests for Phase 2.6 Orchestration & Change Detection."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_6_orchestrate.pipeline import run_ingest, validate_phase2_6  # noqa: E402
from src.ingestion.shared.paths import INGEST_MANIFEST_PATH  # noqa: E402


def test_dry_run_pipeline():
    # Verify that a dry run doesn't mutate files but completes successfully
    status = run_ingest(skip_fetch=True, dry_run=True)
    assert status == 0


def test_full_pipeline_skip_fetch_flow():
    # Remove existing manifest if any to start clean
    if INGEST_MANIFEST_PATH.is_file():
        INGEST_MANIFEST_PATH.unlink()

    # 1. Run pipeline (first run)
    status = run_ingest(skip_fetch=True, force=False)
    assert status == 0
    assert INGEST_MANIFEST_PATH.is_file()

    # Verify post-ingest validations pass
    ok, errors = validate_phase2_6()
    assert ok is True, f"Validation failed: {errors}"

    # Load first run manifest
    with INGEST_MANIFEST_PATH.open(encoding="utf-8") as f:
        manifest_1 = json.load(f)
    assert len(manifest_1["entries"]) == 30

    # 2. Run pipeline (second run - change detection should trigger skips)
    # Since skip_fetch is true and hashes are unchanged, 30/30 should be skipped.
    # We will verify it returns status 0.
    status_2 = run_ingest(skip_fetch=True, force=False)
    assert status_2 == 0

    # 3. Run pipeline (third run - with force, should re-ingest all)
    status_3 = run_ingest(skip_fetch=True, force=True)
    assert status_3 == 0
