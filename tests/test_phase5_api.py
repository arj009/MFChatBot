"""Tests for Phase 5 API and Orchestration Pipeline."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.api.main import app  # noqa: E402
from src.orchestrator.pipeline import MFOrchestratorPipeline  # noqa: E402

client = TestClient(app)


@pytest.fixture
def mock_retrieve_factual():
    with patch("src.orchestrator.pipeline.retrieve") as mock:
        mock.return_value = [
            {
                "id": "c_001",
                "text": "ICICI Prudential Large Cap Fund has an exit load of 1% if redeemed within 1 year.",
                "metadata": {
                    "source_url": "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth",
                    "last_fetched_at": "2026-05-19T00:00:00Z",
                    "scheme_slug": "icici-prudential-large-cap-fund-direct-growth",
                },
                "score": 0.95,
            }
        ]
        yield mock


def test_orchestrator_pii_sweep():
    # Test Aadhaar PII routing and deflection
    pii_query = "My Aadhaar number is 1234-5678-9012, help me invest."
    result = MFOrchestratorPipeline.run_pipeline(pii_query)
    
    assert result["intent"] == "PII_RISK"
    assert result["source_url"] is None
    assert result["last_updated"] is None
    assert "personal identifiers" in result["answer"]


def test_orchestrator_advisory_deflection():
    # Test Advisory routing and deflection
    advisory_query = "Should I invest in ICICI Prudential schemes?"
    result = MFOrchestratorPipeline.run_pipeline(advisory_query)
    
    assert result["intent"] == "ADVISORY"
    assert result["source_url"] is None
    assert "personal investment advice" in result["answer"]
    assert "amfiindia.com" in result["answer"]


def test_orchestrator_performance_deflection(mock_retrieve_factual):
    # Test Performance routing and factsheet deflection
    perf_query = "What will 10000 invested grow to in ICICI Prudential Large Cap Fund?"
    result = MFOrchestratorPipeline.run_pipeline(perf_query)
    
    assert result["intent"] == "PERFORMANCE_CALC"
    assert result["source_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    assert "project returns" in result["answer"]
    assert "Last updated from sources: 2026-05-19" in result["answer"]


def test_api_health_endpoint():
    # Test /api/health endpoint
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "timestamp" in data


def test_api_examples_endpoint():
    # Test /api/examples endpoint
    response = client.get("/api/examples")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 3
    assert data[0]["label"] == "Expense Ratio"
    assert "expense ratio" in data[0]["query"].lower()


def test_api_chat_endpoint_factual(mock_retrieve_factual):
    # Test /api/chat factual query endpoint
    payload = {"query": "What is the exit load of ICICI Prudential Large Cap Fund Direct Growth?"}
    response = client.post("/api/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert data["intent"] == "FACTUAL"
    assert data["source_url"] == "https://groww.in/mutual-funds/icici-prudential-large-cap-fund-direct-growth"
    assert "exit load" in data["answer"].lower()
    assert "latency_ms" in data
