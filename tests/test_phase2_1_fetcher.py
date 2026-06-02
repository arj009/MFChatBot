"""Unit tests for Phase 2.1 fetcher."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.inventory import CorpusEntry, ClosedCorpusError, enforce_closed_url, normalize_url  # noqa: E402
from src.ingestion.phase_2_1_fetch import fetch_entry, raw_basename, raw_html_path  # noqa: E402


def test_raw_basename_with_and_without_slug():
    scheme = CorpusEntry(
        3, "Large Cap", "large_cap",
        "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
        "icici-prudential-large-cap-fund-direct-growth",
        "scheme_page", "approved", "2026-05-18",
    )
    listing = CorpusEntry(
        9, "Listing", "directory",
        "https://groww.in/mutual-funds/filter?fund_house=x",
        None, "amc_listing", "approved", "2026-05-18",
    )
    assert raw_basename(scheme) == "3_icici-prudential-large-cap-fund-direct-growth"
    assert raw_basename(listing) == "9"


def test_enforce_closed_url_rejects_off_list():
    with pytest.raises(ClosedCorpusError):
        enforce_closed_url("https://groww.in/mutual-funds/some-other-fund")


@patch("src.ingestion.phase_2_1_fetch.fetcher.fetch_html")
def test_fetch_entry_writes_html_and_sidecar(mock_fetch_html, tmp_path: Path):
    url = "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    entry = CorpusEntry(
        3, "Large Cap", "large_cap", url,
        "icici-prudential-large-cap-fund-direct-growth",
        "scheme_page", "approved", "2026-05-18",
    )
    mock_fetch_html.return_value = (200, url, "<html><body>Expense Ratio 1.2%</body></html>", [])

    session = MagicMock()
    allowed = frozenset({normalize_url(url)})

    result = fetch_entry(entry, session, allowed, raw_dir=tmp_path, force=True)

    assert result.ok
    assert result.fetch_status == "ok"
    html = raw_html_path(entry, tmp_path)
    meta = tmp_path / "3_icici-prudential-large-cap-fund-direct-growth.meta.json"
    assert html.is_file()
    assert meta.is_file()
    sidecar = json.loads(meta.read_text(encoding="utf-8"))
    assert sidecar["fetch_status"] == "ok"
    assert sidecar["last_fetched_at"]
    assert sidecar["http_status"] == 200
