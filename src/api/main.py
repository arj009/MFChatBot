"""Phase 5 — FastAPI Backend Entrypoint.

Exposes stateless API endpoints to serve chat query processing, health monitoring,
and bootstrap examples for the user interface.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime
from typing import Any

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.orchestrator.pipeline import MFOrchestratorPipeline

# Setup server logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("api.main")

__all__ = ["app"]

app = FastAPI(
    title="ICICI Prudential Mutual Fund Assistant API",
    description="Stateless, compliant, facts-only RAG assistant API built for ICICI Prudential schemes.",
    version="1.0.0",
)

# Enable CORS for local and production cross-origin UI interactions
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permits any origin for absolute frontend flexibility
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 1. Pydantic request / response model schemas
class ChatRequest(BaseModel):
    """Client conversational message payload."""

    query: str | None = Field(None, description="The user query text.")
    message: str | None = Field(None, description="Alternative field name for user query text.")


class ChatResponse(BaseModel):
    """Stateless compliant pipeline output response."""

    answer: str = Field(..., description="Factual answer, advisory deflection, or safe refusal text.")
    source_url: str | None = Field(None, description="Valid citation Groww URL (or None if refusal/PII).")
    intent: str = Field(..., description="The classification intent label routed by the guardrail layer.")
    last_updated: str | None = Field(None, description="Verbatim data freshness date string (or None).")
    latency_ms: float = Field(..., description="End-to-end execution duration in milliseconds.")


# 2. Main conversational route
@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(request: ChatRequest) -> Any:
    """Execute the end-to-end RAG conversational pipeline.

    Main entry point for clients, routing safe requests through the classifier,
    retriever, generator, and validators.
    """
    user_query = request.query or request.message
    if not user_query:
        raise HTTPException(
            status_code=400,
            detail="Request must contain either 'query' or 'message' field.",
        )

    logger.info(f"API Request: Received query of length {len(user_query)}.")
    
    # Process through pipeline orchestrator
    result = MFOrchestratorPipeline.run_pipeline(user_query)
    
    logger.info(f"API Response: Pipeline execution completed in {result['latency_ms']}ms. Intent: {result['intent']}.")
    return result


# 3. Dynamic UI examples route
@app.get("/api/examples")
def examples_endpoint() -> Any:
    """Load and yield three pre-configured example questions for UI chip bootstrapping."""
    config_path = os.path.join("config", "ui_examples.yaml")
    
    default_examples = [
        {
            "label": "Expense Ratio",
            "query": "What is the expense ratio of ICICI Prudential Large Cap Fund Direct Growth?",
        },
        {
            "label": "Minimum SIP",
            "query": "What is the minimum SIP amount for ICICI Prudential Flexicap Fund Direct Growth?",
        },
        {
            "label": "Exit Load",
            "query": "What is the exit load on ICICI Prudential Liquid Fund Direct Plan Growth?",
        },
    ]

    if not os.path.exists(config_path):
        logger.warning(f"ui_examples.yaml not found at {config_path}. Yielding code default examples.")
        return default_examples

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            questions = data.get("questions", [])
            
            # Map labels to questions dynamically
            labels = ["Expense Ratio", "Minimum SIP", "Exit Load"]
            examples = []
            for idx, q in enumerate(questions[:3]):
                label = labels[idx] if idx < len(labels) else "General"
                examples.append({"label": label, "query": q})
                
            return examples if examples else default_examples
    except Exception as e:
        logger.error(f"Failed to read ui_examples.yaml: {e}")
        return default_examples


# 4. Liveness monitoring route
@app.get("/api/health")
def health_endpoint() -> Any:
    """Standard deployment check providing timestamp and liveness indicator."""
    return {
        "status": "ok",
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }
