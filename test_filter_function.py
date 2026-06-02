"""Test the scheme hint filter function."""

from src.retrieval.phase_3_5_filter.filter import find_matching_slugs

# Test various query formats
test_queries = [
    "What is the AUM of ICICI Prudential Large Cap Fund?",
    "Who is the fund manager of ICICI Prudential Large Cap Fund?",
    "What are the top holdings of ICICI Prudential Large Cap Fund?",
    "ICICI Prudential Large Cap Fund",
    "Large Cap Fund",
    "icici-prudential-large-cap-fund-direct-growth",
]

for query in test_queries:
    matches = find_matching_slugs(query)
    print(f"Query: '{query}'")
    print(f"Matches: {matches}")
    print()
