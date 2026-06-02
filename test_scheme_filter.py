"""Test scheme filtering and key facts injection."""

from src.retrieval.retriever import retrieve

# Test with explicit scheme hint
print("=" * 80)
print("TEST 1: AUM query with explicit scheme hint")
print("=" * 80)
chunks = retrieve("What is the AUM?", top_k=3, scheme_hint="ICICI Prudential Large Cap Fund")
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i} (score: {chunk.get('score', 'N/A')}):")
    print(f"Scheme: {chunk.get('metadata', {}).get('scheme_name', 'N/A')}")
    print(f"Chunk index: {chunk.get('metadata', {}).get('chunk_index', 'N/A')}")
    print(f"Text: {chunk['text'][:400]}...")

print("\n" + "=" * 80)
print("TEST 2: Fund manager query with explicit scheme hint")
print("=" * 80)
chunks = retrieve("Who is the fund manager?", top_k=3, scheme_hint="ICICI Prudential Large Cap Fund")
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i} (score: {chunk.get('score', 'N/A')}):")
    print(f"Scheme: {chunk.get('metadata', {}).get('scheme_name', 'N/A')}")
    print(f"Chunk index: {chunk.get('metadata', {}).get('chunk_index', 'N/A')}")
    print(f"Text: {chunk['text'][:400]}...")

print("\n" + "=" * 80)
print("TEST 3: AUM query with slug hint")
print("=" * 80)
chunks = retrieve("What is the AUM?", top_k=3, scheme_hint="icici-prudential-large-cap-fund-direct-growth")
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i} (score: {chunk.get('score', 'N/A')}):")
    print(f"Scheme: {chunk.get('metadata', {}).get('scheme_name', 'N/A')}")
    print(f"Chunk index: {chunk.get('metadata', {}).get('chunk_index', 'N/A')}")
    print(f"Text: {chunk['text'][:400]}...")

print("\n" + "=" * 80)
print("TEST 4: AUM query without scheme hint")
print("=" * 80)
chunks = retrieve("What is the AUM of ICICI Prudential Large Cap Fund?", top_k=3, scheme_hint=None)
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i} (score: {chunk.get('score', 'N/A')}):")
    print(f"Scheme: {chunk.get('metadata', {}).get('scheme_name', 'N/A')}")
    print(f"Chunk index: {chunk.get('metadata', {}).get('chunk_index', 'N/A')}")
    print(f"Text: {chunk['text'][:400]}...")
