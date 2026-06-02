"""Tests for Phase 4.4 Performance-Query Path Deflection."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generation.performance import MFPerformanceHandler  # noqa: E402


def test_resolve_exact_scheme_url():
    # Fuzzy match should resolve large cap fund URL
    query_1 = "What are the 3-year returns of ICICI Prudential Large Cap Fund?"
    url_1 = MFPerformanceHandler.resolve_scheme_url(query_1)
    
    assert url_1 == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"

    # Fuzzy match should resolve flexicap fund URL
    query_2 = "What will 10000 grow to in ICICI Prudential Flexicap Fund?"
    url_2 = MFPerformanceHandler.resolve_scheme_url(query_2)
    
    assert url_2 == "https://groww.in/mutual-funds/icici-prudential-flexicap-fund-direct-growth"


def test_resolve_fallback_listing_url():
    # Generic performance queries with no specific scheme mentioned
    query = "What will 10000 invested grow to in 5 years?"
    url = MFPerformanceHandler.resolve_scheme_url(query)
    
    # Defaults to general ICICI Prudential mutual fund list on Groww
    assert "mutual-funds/filter" in url
    assert "ICICI+Prudential+Mutual+Fund" in url


def test_generate_performance_deflection():
    query = "What is the CAGR of ICICI Large Cap?"
    mock_chunks = [
        {
            "metadata": {
                "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
                "last_fetched_at": "2026-05-19T00:00:00Z",
            }
        }
    ]

    response_text, citation_url = MFPerformanceHandler.generate_performance_response(
        query=query,
        retrieved_chunks=mock_chunks,
    )

    assert "project returns" in response_text
    assert citation_url == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    assert citation_url in response_text
    assert "Last updated from sources: 2026-05-19" in response_text
