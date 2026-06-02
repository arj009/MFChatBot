#!/usr/bin/env python3
"""Test the full orchestrator pipeline with NAV queries."""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

from src.orchestrator.pipeline import MFOrchestratorPipeline

# Test NAV queries
test_queries = [
    "What is the NAV of ICICI Prudential Nifty Index Fund?",
    "NAV of ICICI Prudential Nifty Index Fund",
    "ICICI Nifty50 index fund NAV",
]

print("Testing full orchestrator pipeline for NAV queries:")
print("=" * 60)

for query in test_queries:
    print(f"\nQuery: '{query}'")
    try:
        result = MFOrchestratorPipeline.run_pipeline(query)
        print(f"Intent: {result.get('intent', 'N/A')}")
        print(f"Answer: {result.get('answer', 'N/A')[:300]}...")
        print(f"Source URL: {result.get('source_url', 'N/A')}")
        print(f"Latency: {result.get('latency_ms', 'N/A')}ms")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
