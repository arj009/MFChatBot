"""Tests for Phase 2.3 normalizer."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_3_normalize.normalizer import (  # noqa: E402
    compute_content_hash,
    normalize_text,
)


def test_compute_content_hash_stable():
    h1 = compute_content_hash("hello")
    h2 = compute_content_hash("hello")
    assert h1 == h2
    assert len(h1) == 64


def test_normalize_text_collapses_whitespace():
    parsed = {
        "full_text": "# Fund\n\n## Key facts\nExpense ratio: 1.06%\n\n\n\nExit load: none",
    }
    out = normalize_text(parsed)
    assert "Expense ratio" in out
    assert "\n\n\n" not in out
