"""Test pipeline-style retrieval with full query as scheme_hint."""

from src.retrieval.retriever import retrieve

# Test exactly as the pipeline does
query = "What is the AUM of ICICI Prudential Large Cap Fund?"
print(f"Query: '{query}'")
print("=" * 80)

chunks = retrieve(query, top_k=3, scheme_hint=query)
print(f"Found {len(chunks)} chunks")

for i, chunk in enumerate(chunks):
    print(f"\nChunk {i} (score: {chunk.get('score', 'N/A')}):")
    print(f"Scheme: {chunk.get('metadata', {}).get('scheme_name', 'N/A')}")
    print(f"Chunk index: {chunk.get('metadata', {}).get('chunk_index', 'N/A')}")
    print(f"Text preview: {chunk['text'][:300]}...")
    
    # Check if this chunk contains AUM or manager
    text_lower = chunk['text'].lower()
    if 'aum' in text_lower:
        print(">>> CONTAINS AUM")
    if 'manager' in text_lower:
        print(">>> CONTAINS MANAGER")
