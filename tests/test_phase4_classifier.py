"""Tests for Phase 4.1 Query Classifier."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.guardrails.classifier import MFQueryClassifier  # noqa: E402


def test_pii_aadhaar_sweep():
    # Aadhaar patterns with spaces/hyphens
    query_1 = "My Aadhaar number is 1234 5678 9012. Can you help me?"
    query_2 = "Aadhaar: 9876-5432-1098"
    query_3 = "Just a general number 123456789012 without spacing context is fine."

    assert MFQueryClassifier.classify(query_1) == "PII_RISK"
    assert MFQueryClassifier.classify(query_2) == "PII_RISK"
    # Single contiguous 12-digit number without spacing is also blocked for security
    assert MFQueryClassifier.classify("123456789012") == "PII_RISK"


def test_pii_pan_sweep():
    # PAN Card uppercase alphanumeric format
    query_1 = "Here is my PAN Card details: ABCDE1234F"
    query_2 = "pan number is abcde5678g"

    assert MFQueryClassifier.classify(query_1) == "PII_RISK"
    assert MFQueryClassifier.classify(query_2) == "PII_RISK"


def test_pii_email_phone_sweep():
    # Phone numbers and email addresses
    query_email = "Please contact me at test_user@example.com."
    query_phone_1 = "My mobile is +91 9876543210"
    query_phone_2 = "Call me on 9123456789"

    assert MFQueryClassifier.classify(query_email) == "PII_RISK"
    assert MFQueryClassifier.classify(query_phone_1) == "PII_RISK"
    assert MFQueryClassifier.classify(query_phone_2) == "PII_RISK"


def test_pii_otp_sweep():
    # OTP or verification codes
    query_otp_1 = "My transaction OTP is 584930"
    query_otp_2 = "verification code: 1234"

    assert MFQueryClassifier.classify(query_otp_1) == "PII_RISK"
    assert MFQueryClassifier.classify(query_otp_2) == "PII_RISK"


def test_fallback_performance_calc():
    # Verify performance deflection routing triggers on keywords
    query_1 = "What will 10k grow to in 5 years?"
    query_2 = "Calculate returns of ICICI Prudential Large Cap Fund."
    query_3 = "What is the 5-year CAGR?"

    assert MFQueryClassifier.classify(query_1) == "PERFORMANCE_CALC"
    assert MFQueryClassifier.classify(query_2) == "PERFORMANCE_CALC"
    assert MFQueryClassifier.classify(query_3) == "PERFORMANCE_CALC"


def test_fallback_comparative():
    # Verify comparison deflection routing triggers on keywords
    query_1 = "Which fund is better: Large Cap vs Bluechip?"
    query_2 = "ICICI Prudential Flexicap Fund compared to Liquid Fund"
    query_3 = "Is midcap a better choice than large cap?"

    assert MFQueryClassifier.classify(query_1) == "COMPARATIVE"
    assert MFQueryClassifier.classify(query_2) == "COMPARATIVE"
    assert MFQueryClassifier.classify(query_3) == "COMPARATIVE"


def test_fallback_advisory():
    # Verify advisory deflection routing triggers on keywords
    query_1 = "Should I invest in ICICI Prudential Large Cap?"
    query_2 = "Can you suggest a fund for my retirement?"
    query_3 = "Give me some financial advice."

    assert MFQueryClassifier.classify(query_1) == "ADVISORY"
    assert MFQueryClassifier.classify(query_2) == "ADVISORY"
    assert MFQueryClassifier.classify(query_3) == "ADVISORY"


def test_fallback_out_of_scope():
    # Verify out of scope triggers on generic chit-chat or external names
    query_1 = "What is the weather in Delhi?"
    query_2 = "Tell me a funny joke."
    query_3 = "How is Reliance stock doing today?"

    assert MFQueryClassifier.classify(query_1) == "OUT_OF_SCOPE"
    assert MFQueryClassifier.classify(query_2) == "OUT_OF_SCOPE"
    assert MFQueryClassifier.classify(query_3) == "OUT_OF_SCOPE"


def test_fallback_factual():
    # Verify standard factual questions route to FACTUAL
    query_1 = "What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?"
    query_2 = "Who is the fund manager of Flexicap?"
    query_3 = "What is the exit load on Liquid Fund?"

    assert MFQueryClassifier.classify(query_1) == "FACTUAL"
    assert MFQueryClassifier.classify(query_2) == "FACTUAL"
    assert MFQueryClassifier.classify(query_3) == "FACTUAL"
