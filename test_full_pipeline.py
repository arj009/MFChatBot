"""Test the full pipeline with AUM and fund manager queries."""

from src.orchestrator.pipeline import MFOrchestratorPipeline

# Test AUM query
print("=" * 80)
print("TEST 1: AUM Query")
print("=" * 80)
result = MFOrchestratorPipeline.run_pipeline("What is the AUM of ICICI Prudential Large Cap Fund?")
print(f"Intent: {result['intent']}")
print(f"Answer: {result['answer']}")
print(f"Source URL: {result['source_url']}")
print(f"Last Updated: {result['last_updated']}")
print(f"Latency: {result['latency_ms']}ms")

print("\n" + "=" * 80)
print("TEST 2: Fund Manager Query")
print("=" * 80)
result = MFOrchestratorPipeline.run_pipeline("Who is the fund manager of ICICI Prudential Large Cap Fund?")
print(f"Intent: {result['intent']}")
print(f"Answer: {result['answer']}")
print(f"Source URL: {result['source_url']}")
print(f"Last Updated: {result['last_updated']}")
print(f"Latency: {result['latency_ms']}ms")

print("\n" + "=" * 80)
print("TEST 3: Top Holdings Query")
print("=" * 80)
result = MFOrchestratorPipeline.run_pipeline("What are the top holdings of ICICI Prudential Large Cap Fund?")
print(f"Intent: {result['intent']}")
print(f"Answer: {result['answer']}")
print(f"Source URL: {result['source_url']}")
print(f"Last Updated: {result['last_updated']}")
print(f"Latency: {result['latency_ms']}ms")
