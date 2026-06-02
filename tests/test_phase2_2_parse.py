"""Tests for Phase 2.2 parser."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import CorpusEntry  # noqa: E402
from src.ingestion.phase_2_2_parse.parser import _build_scheme_document  # noqa: E402
from src.ingestion.shared.next_data import extract_next_data, page_props  # noqa: E402

FIXTURE = ROOT / "tests" / "fixtures" / "sample_scheme.html"


@pytest.fixture
def sample_html() -> str:
    if FIXTURE.is_file():
        return FIXTURE.read_text(encoding="utf-8")
    pytest.skip("fixture missing — run fetch for scheme #3 first")


def test_extract_next_data(sample_html: str):
    assert extract_next_data(sample_html) is not None
    props = page_props(sample_html)
    assert props and "mfServerSideData" in props


def test_build_scheme_document(sample_html: str):
    entry = CorpusEntry(
        3, "ICICI Prudential Large Cap Fund Direct Growth", "large_cap",
        "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "icici-prudential-large-cap-fund-direct-growth",
        "scheme_page", "approved", "2026-05-18",
    )
    mf = page_props(sample_html)["mfServerSideData"]
    doc = _build_scheme_document(entry, sample_html, mf, "Test Title")
    assert doc.key_facts.get("expense_ratio")
    assert "expense ratio" in doc.full_text.lower()
    assert doc.sections
