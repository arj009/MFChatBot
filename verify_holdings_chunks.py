"""Verify holdings data in chunks."""

import json

chunks = [json.loads(line) for line in open('data/chunks/chunk_store.jsonl', 'r', encoding='utf-8')]
holdings_chunks = [c for c in chunks if 'holding' in c.get('text', '').lower()]
large_cap_holdings = [c for c in holdings_chunks if c.get('scheme_slug') and 'large-cap' in c.get('scheme_slug', '').lower()]

print(f'Total chunks: {len(chunks)}')
print(f'Chunks with holding: {len(holdings_chunks)}')
print(f'Large Cap holdings chunks: {len(large_cap_holdings)}')

for c in large_cap_holdings:
    print(f"\nChunk {c['chunk_index']}:")
    print(c['text'])
