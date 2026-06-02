#!/usr/bin/env python3
"""Check if chunk_index 0 chunks exist in vector DB."""

import chromadb

client = chromadb.PersistentClient(path='data/index')
col = client.get_collection('mf_chunks')
results = col.get(where={'chunk_index': 0})
print(f'Found {len(results["ids"])} chunks with chunk_index 0')
if len(results["ids"]) > 0:
    print(f'First chunk_index 0 ID: {results["ids"][0]}')
    print(f'Scheme: {results["metadatas"][0].get("scheme_name", "N/A")}')
