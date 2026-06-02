"""Unit tests for Phase 1 corpus curation."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.corpus.curation import (  # noqa: E402
    detect_blocked_content,
    scan_fact_signals,
    scheme_names_align,
    validate_amc_listing,
)
from src.corpus.inventory import is_allowed_url, normalize_url  # noqa: E402


def test_normalize_url_preserves_filter_query():
    url = "https://groww.in/mutual-funds/filter?fund_house=%5B%22ICICI+Prudential+Mutual+Fund%22%5D"
    assert "fund_house=" in normalize_url(url)


def test_closed_list_rejects_other_groww_page():
    allowed = "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    other = "https://groww.in/mutual-funds/hdfc-flexi-cap-fund-direct-growth"
    assert is_allowed_url(allowed)
    assert not is_allowed_url(other)


def test_detect_blocked_content():
    assert detect_blocked_content("<html>Please complete the CAPTCHA</html>")
    assert not detect_blocked_content("<html>Expense ratio 0.5%</html>")


def test_scan_fact_signals_finds_expense_ratio():
    html = "<div>Expense Ratio</motion.div><div>Exit Load</motion.div>"
    found, gaps = scan_fact_signals(html, "scheme_page")
    assert found["expense_ratio"] is True
    assert "expense_ratio" not in gaps


def test_amc_listing_markers():
    assert validate_amc_listing("<html>ICICI Prudential Mutual Fund schemes</html>")
    assert not validate_amc_listing("<html>HDFC Mutual Fund</html>")


def test_scheme_names_align():
    inv = "ICICI Prudential Large Cap Fund Direct Growth"
    title = "ICICI Prudential Large Cap Fund Direct Growth - Groww"
    assert scheme_names_align(inv, title) is True
