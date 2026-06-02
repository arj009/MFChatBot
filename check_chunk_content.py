"""Check actual chunk content for AUM, fund manager, and holdings."""

import json

chunks = [json.loads(line) for line in open('data/chunks/chunk_store.jsonl', 'r', encoding='utf-8')]

# Find Large Cap Fund chunks
large_cap_chunks = [c for c in chunks if c.get('scheme_slug') and 'large-cap' in c.get('scheme_slug', '').lower()]

print(f"Total Large Cap chunks: {len(large_cap_chunks)}")
print("\n" + "=" * 80)

# Show all chunks for Large Cap Fund
for i, chunk in enumerate(large_cap_chunks):
    print(f"\nChunk {i} (index {chunk['chunk_index']}):")
    print(f"Text length: {len(chunk['text'])}")
    print(f"Text preview:\n{chunk['text'][:600]}")
    print("\n" + "-" * 80)

# Check for AUM in all chunks
print("\n" + "=" * 80)
print("CHUNKS CONTAINING 'AUM':")
print("=" * 80)
aum_chunks = [c for c in chunks if 'aum' in c.get('text', '').lower()]
print(f"Found {len(aum_chunks)} chunks with AUM")
for i, chunk in enumerate(aum_chunks[:5]):
    print(f"\nChunk {i}: {chunk['scheme_name']}")
    print(f"Text: {chunk['text'][:400]}")

# Check for fund manager in all chunks
print("\n" + "=" * 80)
print("CHUNKS CONTAINING 'MANAGER':")
print("=" * 80)
manager_chunks = [c for c in chunks if 'manager' in c.get('text', '').lower()]
print(f"Found {len(manager_chunks)} chunks with manager")
for i, chunk in enumerate(manager_chunks[:5]):
    print(f"\nChunk {i}: {chunk['scheme_name']}")
    print(f"Text: {chunk['text'][:400]}")

# Check for holdings in all chunks
print("\n" + "=" * 80)
print("CHUNKS CONTAINING 'HOLDING':")
print("=" * 80)
holding_chunks = [c for c in chunks if 'holding' in c.get('text', '').lower()]
print(f"Found {len(holding_chunks)} chunks with holding")
