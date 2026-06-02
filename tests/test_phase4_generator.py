"""Tests for Phase 4.3 Constrained Generator and Response Validator."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.generation.generator import MFGenerator  # noqa: E402
from src.guardrails.validator import MFResponseValidator  # noqa: E402


@pytest.fixture
def mock_retrieved_chunks():
    return [
        {
            "id": "c_001",
            "text": "ICICI Prudential Large Cap Fund is an open-ended equity scheme. The exit load is 1% if redeemed within 1 year. The fund manager is Mr. Anish Tawakley.",
            "metadata": {
                "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
                "last_fetched_at": "2026-05-18T10:00:00Z",
                "scheme_slug": "icici-prudential-large-cap-fund-direct-growth",
            },
            "score": 0.95,
        },
        {
            "id": "c_002",
            "text": "The minimum SIP investment is Rs. 100. The expense ratio is 0.92% direct growth.",
            "metadata": {
                "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
                "last_fetched_at": "2026-05-19T08:00:00Z",
                "scheme_slug": "icici-prudential-large-cap-fund-direct-growth",
            },
            "score": 0.88,
        },
    ]


def test_validator_sentence_truncation(mock_retrieved_chunks):
    # Text with 5 sentences
    input_text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    fallback_url = mock_retrieved_chunks[0]["metadata"]["source_url"]

    fixed_text, citation_url, is_valid = MFResponseValidator.validate_and_fix(
        text=input_text,
        retrieved_chunks=mock_retrieved_chunks,
        fallback_url=fallback_url,
    )

    # Check that sentences are truncated to exactly 3
    assert is_valid
    assert "Sentence four" not in fixed_text
    assert "Sentence one. Sentence two. Sentence three." in fixed_text
    assert citation_url == fallback_url


def test_validator_no_url_injection(mock_retrieved_chunks):
    # Text with zero URLs
    input_text = "The exit load on this scheme is 1% if redeemed within 1 year."
    fallback_url = mock_retrieved_chunks[0]["metadata"]["source_url"]

    fixed_text, citation_url, is_valid = MFResponseValidator.validate_and_fix(
        text=input_text,
        retrieved_chunks=mock_retrieved_chunks,
        fallback_url=fallback_url,
    )

    assert is_valid
    assert fallback_url in fixed_text
    assert citation_url == fallback_url


def test_validator_multiple_urls_deduplication(mock_retrieved_chunks):
    # Text with multiple URLs (some unapproved)
    fallback_url = mock_retrieved_chunks[0]["metadata"]["source_url"]
    input_text = f"The exit load details are on {fallback_url} and also see unapproved http://google.com link."

    fixed_text, citation_url, is_valid = MFResponseValidator.validate_and_fix(
        text=input_text,
        retrieved_chunks=mock_retrieved_chunks,
        fallback_url=fallback_url,
    )

    assert is_valid
    assert fallback_url in fixed_text
    assert "google.com" not in fixed_text
    assert citation_url == fallback_url


def test_validator_advisory_sweep(mock_retrieved_chunks):
    # Text containing non-compliant financial advice terms
    input_text = "I recommend that you should invest in this scheme because it is the best option."
    fallback_url = mock_retrieved_chunks[0]["metadata"]["source_url"]

    fixed_text, citation_url, is_valid = MFResponseValidator.validate_and_fix(
        text=input_text,
        retrieved_chunks=mock_retrieved_chunks,
        fallback_url=fallback_url,
    )

    # Should deflect to advisory refusal template
    assert not is_valid
    assert "personal investment advice" in fixed_text
    assert citation_url is None


def test_validator_freshness_footer_date(mock_retrieved_chunks):
    # Checks max(last_fetched_at) from retrieved_chunks metadata.
    # mock_retrieved_chunks contains dates: '2026-05-18T10:00:00Z' and '2026-05-19T08:00:00Z'.
    # Maximum should be '2026-05-19'.
    input_text = "Factual answer text."
    fallback_url = mock_retrieved_chunks[0]["metadata"]["source_url"]

    fixed_text, citation_url, is_valid = MFResponseValidator.validate_and_fix(
        text=input_text,
        retrieved_chunks=mock_retrieved_chunks,
        fallback_url=fallback_url,
    )

    assert is_valid
    assert "Last updated from sources: 2026-05-19" in fixed_text


def test_generator_offline_factual_response(mock_retrieved_chunks):
    # Verify the fallback offline generation logic works cleanly
    query = "What is the exit load?"
    fixed_text, citation_url = MFGenerator.generate_factual_response(
        query=query,
        retrieved_chunks=mock_retrieved_chunks,
    )

    assert fixed_text is not None
    assert "exit load" in fixed_text.lower()
    assert citation_url == mock_retrieved_chunks[0]["metadata"]["source_url"]
    assert "Last updated from sources: 2026-05-19" in fixed_text
