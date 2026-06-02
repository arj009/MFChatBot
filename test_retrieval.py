#!/usr/bin/env python3
"""Test retrieval for NAV queries."""

import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[0]
sys.path.insert(0, str(ROOT))

# Set logging level to DEBUG to see retriever logs
logging.basicConfig(level=logging.DEBUG)

from src.retrieval.retriever import retrieve

# Test NAV queries with scheme hints
test_cases = [
    ("What is the NAV of ICICI Nifty Index Fund?", "ICICI Nifty Index Fund"),
    ("NAV of ICICI Prudential Nifty Index Fund", "ICICI Prudential Nifty Index Fund"),
    ("ICICI Nifty50 index fund NAV", "ICICI Nifty50 index fund"),
]

print("Testing retrieval for NAV queries:")
print("=" * 60)

for query, scheme_hint in test_cases:
    print(f"\nQuery: '{query}'")
    print(f"Scheme hint: '{scheme_hint}'")
    try:
        results = retrieve(query, top_k=3, scheme_hint=scheme_hint)
        print(f"Found {len(results)} chunks")
        for i, chunk in enumerate(results):
            print(f"\nChunk {i+1}:")
            print(f"Score: {chunk.get('score', 'N/A')}")
            print(f"Scheme: {chunk.get('metadata', {}).get('scheme_name', 'N/A')}")
            print(f"Chunk index: {chunk.get('metadata', {}).get('chunk_index', 'N/A')}")
            text_preview = chunk.get('text', '')[:300]
            if "Key facts" in text_preview:
                text_preview = text_preview[:300] + " [KEY FACTS]"
            print(f"Text preview: {text_preview}...")
    except Exception as e:
        print(f"Error: {e}")

print("\n" + "=" * 60)
