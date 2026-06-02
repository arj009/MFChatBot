"""Test retrieval for AUM, fund manager, and holdings queries."""

from src.retrieval.retriever import retrieve

# Test AUM query
print("=" * 60)
print("TEST 1: AUM Query")
print("=" * 60)
chunks = retrieve("What is the AUM of ICICI Prudential Large Cap Fund?", top_k=3)
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"Text: {chunk['text'][:300]}...")
    print(f"Source: {chunk.get('source_url', 'N/A')}")

# Test Fund Manager query
print("\n" + "=" * 60)
print("TEST 2: Fund Manager Query")
print("=" * 60)
chunks = retrieve("Who is the fund manager of ICICI Prudential Large Cap Fund?", top_k=3)
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"Text: {chunk['text'][:300]}...")
    print(f"Source: {chunk.get('source_url', 'N/A')}")

# Test Top Holdings query
print("\n" + "=" * 60)
print("TEST 3: Top Holdings Query")
print("=" * 60)
chunks = retrieve("What are the top holdings of ICICI Prudential Large Cap Fund?", top_k=3)
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"Text: {chunk['text'][:300]}...")
    print(f"Source: {chunk.get('source_url', 'N/A')}")

# Test simple keyword queries
print("\n" + "=" * 60)
print("TEST 4: Simple AUM keyword")
print("=" * 60)
chunks = retrieve("AUM", top_k=3)
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"Text: {chunk['text'][:300]}...")
    print(f"Source: {chunk.get('source_url', 'N/A')}")

print("\n" + "=" * 60)
print("TEST 5: Simple fund manager keyword")
print("=" * 60)
chunks = retrieve("fund manager", top_k=3)
print(f"Found {len(chunks)} chunks")
for i, chunk in enumerate(chunks):
    print(f"\nChunk {i}:")
    print(f"Text: {chunk['text'][:300]}...")
    print(f"Source: {chunk.get('source_url', 'N/A')}")
