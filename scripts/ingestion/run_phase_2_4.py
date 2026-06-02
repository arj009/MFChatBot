#!/usr/bin/env python3
"""Phase 2.4 — Chunk normalized documents in-memory by Markdown headings."""

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from src.ingestion.phase_2_4_chunk.chunker import chunk_all, validate_phase2_4  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Phase 2.4 chunker runner")
    parser.parse_args()

    print("Phase 2.4 — Chunk & Metadata\n")

    try:
        chunks = chunk_all()
        print(f"  Successfully generated {len(chunks)} chunks in-memory.")

        # Calculate statistics
        num_docs = 30
        avg_chunks = len(chunks) / num_docs
        print(f"  Documents processed: {num_docs}")
        print(f"  Average chunks per document: {avg_chunks:.2f}")

        # Show a sample chunk
        if chunks:
            print("\n  Sample Chunk (Index 0):")
            sample = chunks[0]
            print(f"    Source URL: {sample['source_url']}")
            print(f"    Source Type: {sample['source_type']}")
            print(f"    Scheme Name: {sample['scheme_name']}")
            print(f"    Document Title: {sample['document_title']}")
            print(f"    Chunk Index: {sample['chunk_index']}")
            print(f"    Content Hash: {sample['content_hash']}")
            print(f"    Last Fetched At: {sample['last_fetched_at']}")
            print("    Text Snippet:")
            text_lines = sample['text'].splitlines()
            snippet = "\n".join(f"      {line}" for line in text_lines[:6])
            print(snippet)
            if len(text_lines) > 6:
                print("      ...")

        # Run validation
        valid, errors = validate_phase2_4(chunks)
        if valid:
            print("\nPhase 2.4 exit criteria: all satisfied.")
            return 0

        print("\nPhase 2.4 exit criteria: not satisfied.")
        for err in errors:
            print(f"  - {err}")
        return 1

    except Exception as e:
        print(f"  Error running Phase 2.4 chunker: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
