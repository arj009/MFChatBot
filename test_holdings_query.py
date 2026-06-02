"""Test holdings query with the updated pipeline."""

from src.orchestrator.pipeline import MFOrchestratorPipeline

# Test Top Holdings query
print("=" * 80)
print("TEST: Top Holdings Query")
print("=" * 80)
result = MFOrchestratorPipeline.run_pipeline("What are the top holdings of ICICI Prudential Large Cap Fund?")
print(f"Intent: {result['intent']}")
print(f"Answer: {result['answer']}")
print(f"Source URL: {result['source_url']}")
print(f"Last Updated: {result['last_updated']}")
print(f"Latency: {result['latency_ms']}ms")
