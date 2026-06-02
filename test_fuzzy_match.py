#!/usr/bin/env python3
"""Test script to verify fuzzy matching for scheme names."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

from src.retrieval.phase_3_5_filter.filter import find_matching_slugs

# Test cases for fuzzy matching
test_cases = [
    ("ICICI Nifty50 index fund", "Should match Nifty Index Fund"),
    ("nifty50", "Should match Nifty Index Fund"),
    ("nifty index fund", "Should match Nifty Index Fund"),
    ("ICICI Prudential Nifty Index Fund", "Should match Nifty Index Fund"),
    ("largecap", "Should match Large Cap funds"),
    ("flexicap", "Should match Flexicap Fund"),
    ("midcap", "Should match Midcap Fund"),
]

print("Testing fuzzy matching logic:")
print("=" * 60)

for query, description in test_cases:
    matches = find_matching_slugs(query)
    print(f"Query: '{query}'")
    print(f"Description: {description}")
    print(f"Matches: {matches}")
    print()

print("=" * 60)
print("Test completed.")
