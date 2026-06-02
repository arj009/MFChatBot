"""Tests for Phase 4.2 Refusal Handler."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.guardrails.refusal import MFRefusalHandler  # noqa: E402


def test_advisory_refusal():
    # Verify advisory refusal template loads and injects educational link
    resp = MFRefusalHandler.get_refusal_response("ADVISORY")
    
    assert "personal investment advice" in resp
    assert "AMFI — Mutual Fund investor information" in resp
    assert "https://www.amfiindia.com/investor" in resp
    assert resp.startswith("I can only share")


def test_comparative_refusal():
    # Verify comparative refusal template loads and injects educational link
    resp = MFRefusalHandler.get_refusal_response("COMPARATIVE")
    
    assert "compare funds" in resp
    assert "AMFI" in resp
    assert "https://www.amfiindia.com/investor" in resp


def test_out_of_scope_refusal():
    # Verify out of scope refusal template loads and injects educational link
    resp = MFRefusalHandler.get_refusal_response("OUT_OF_SCOPE")
    
    assert "question isn’t covered" in resp
    assert "AMFI" in resp
    assert "https://www.amfiindia.com/investor" in resp


def test_pii_risk_block_no_url():
    # Verify PII risk response has NO URL or educational link whatsoever
    resp = MFRefusalHandler.get_refusal_response("PII_RISK")
    
    assert "don’t share personal identifiers" in resp
    assert "PAN, Aadhaar" in resp
    assert "http" not in resp  # Strictly no links
    assert "educational_link" not in resp


def test_performance_calc_deflection():
    # Verify performance calc deflection formats scheme_link and date footer
    test_link = "https://groww.in/mutual-funds/test-scheme-url"
    test_date = "2026-05-19"
    resp = MFRefusalHandler.get_refusal_response("PERFORMANCE_CALC", scheme_link=test_link, date=test_date)
    
    assert "can’t project returns" in resp
    assert test_link in resp
    assert f"Last updated from sources: {test_date}" in resp

    # Check fallback defaults
    resp_fallback = MFRefusalHandler.get_refusal_response("PERFORMANCE_CALC")
    assert "groww.in/mutual-funds/filter" in resp_fallback
    assert "Last updated from sources: 2026-05-18" in resp_fallback
