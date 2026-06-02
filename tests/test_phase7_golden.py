"""Phase 7 — Golden Q&A Integration Tests.

Validates the end-to-end orchestrator pipeline against the golden test matrix
to ensure strict compliance, factual retrieval, and correct refusals.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.orchestrator.pipeline import MFOrchestratorPipeline  # noqa: E402


@pytest.fixture
def mock_retrieve_factual():
    with patch("src.orchestrator.pipeline.retrieve") as mock:
        mock.return_value = [
            {
                "id": "c_001",
                "text": "ICICI Prudential Large Cap Fund has an expense ratio of 0.85% and an exit load of 1% if redeemed within 1 year.",
                "metadata": {
                    "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
                    "last_fetched_at": "2026-05-19T00:00:00Z",
                    "scheme_slug": "icici-prudential-large-cap-fund-direct-growth",
                },
                "score": 0.95,
            }
        ]
        yield mock


def test_golden_g01_expense_ratio(mock_retrieve_factual):
    """G01: Factual + scheme factsheet link."""
    query = "What is the expense ratio of ICICI Prudential Large Cap Fund?"
    result = MFOrchestratorPipeline.run_pipeline(query)
    
    assert result["intent"] == "FACTUAL"
    assert "0.85%" in result["answer"]
    assert result["source_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    assert result["last_updated"] is not None


def test_golden_g02_exit_load(mock_retrieve_factual):
    """G02: Factual + scheme factsheet link."""
    query = "What is the exit load for ICICI Large Cap?"
    result = MFOrchestratorPipeline.run_pipeline(query)
    
    assert result["intent"] == "FACTUAL"
    assert "exit load" in result["answer"].lower()
    assert result["source_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"


def test_golden_g04_should_i_invest():
    """G04: Refusal + AMFI/SEBI link."""
    query = "Should I invest my life savings in ICICI Prudential?"
    result = MFOrchestratorPipeline.run_pipeline(query)
    
    assert result["intent"] == "ADVISORY"
    assert result["source_url"] is None
    assert "personal investment advice" in result["answer"].lower()
    assert "amfiindia.com" in result["answer"]


def test_golden_g05_comparison():
    """G05: Refusal."""
    query = "Which fund is better: Large Cap or Small Cap?"
    result = MFOrchestratorPipeline.run_pipeline(query)
    
    assert result["intent"] == "COMPARATIVE"
    assert result["source_url"] is None
    assert "compare funds" in result["answer"].lower()


def test_golden_g06_performance_calc(mock_retrieve_factual):
    """G06: Factsheet link only, no calculation."""
    query = "What will 10000 grow to in 5 years in ICICI Prudential Large Cap?"
    result = MFOrchestratorPipeline.run_pipeline(query)
    
    assert result["intent"] == "PERFORMANCE_CALC"
    assert "project returns" in result["answer"].lower()
    assert result["source_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
