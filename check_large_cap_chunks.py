"""Check all Large Cap chunks to see what data is available."""

import json

chunks = [json.loads(line) for line in open('data/chunks/chunk_store.jsonl', 'r', encoding='utf-8')]
large_cap_chunks = [c for c in chunks if c.get('scheme_slug') and 'large-cap' in c.get('scheme_slug', '').lower()]

print('=== ALL LARGE CAP CHUNKS ===')
for c in large_cap_chunks:
    print(f"\nChunk {c['chunk_index']}:")
    print(c['text'])
