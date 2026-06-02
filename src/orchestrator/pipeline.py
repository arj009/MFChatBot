"""Phase 5 — Orchestration Pipeline.

Wires together the query classifier, refusal handler, semantic retrieval layer,
LLM generator, and post-validation checks into a single atomic execution pipeline.
"""

from __future__ import annotations

import hashlib
import logging
import re
import time
from typing import Any

from src.generation.generator import MFGenerator
from src.generation.performance import MFPerformanceHandler
from src.guardrails.classifier import MFQueryClassifier
from src.guardrails.refusal import MFRefusalHandler
from src.retrieval.retriever import retrieve

logger = logging.getLogger("orchestrator.pipeline")

__all__ = ["MFOrchestratorPipeline"]


class MFOrchestratorPipeline:
    """Coordinates conversational requests across all guardrail, retrieval, and generation subsystems."""

    @classmethod
    def run_pipeline(cls, query: str) -> dict[str, Any]:
        """Execute the full conversational pipeline for a given user query.

        Args:
            query: Raw user query string.

        Returns:
            A structured dictionary matching the API response contract:
                - answer (str): Factual answer, educational deflection, or refusal copy.
                - source_url (str | None): Citation Groww URL, AMC list, or None.
                - intent (str): Routed classification category label.
                - last_updated (str | None): Verbatim freshness date footer or None.
                - latency_ms (float): End-to-end execution duration.
        """
        start_time = time.perf_counter()
        
        # 1. Sanitize raw input
        sanitized_query = query.strip()
        query_hash = hashlib.sha256(sanitized_query.encode("utf-8")).hexdigest()[:8]
        
        # Enforce reasonable input bounds (e.g. maximum 500 characters)
        if len(sanitized_query) > 500:
            logger.warning(f"Query {query_hash} exceeded length limits (len={len(sanitized_query)}). Truncating.")
            sanitized_query = sanitized_query[:500]

        logger.info(f"Pipeline started for query hash: {query_hash}")

        try:
            # 2. PII / Security Sweep - Bypasses LLMs and Vector Store completely for safety
            if MFQueryClassifier.detect_pii_risk(sanitized_query):
                logger.warning(f"Query {query_hash} flagged for PII risk. Deflecting instantly.")
                answer = MFRefusalHandler.get_refusal_response("PII_RISK")
                latency = (time.perf_counter() - start_time) * 1000
                return {
                    "answer": answer,
                    "source_url": None,
                    "intent": "PII_RISK",
                    "last_updated": None,
                    "latency_ms": round(latency, 2),
                }

            # 3. Intent Classification
            intent = MFQueryClassifier.classify(sanitized_query)
            logger.info(f"Query {query_hash} classified as intent: {intent}")

            # 4. Pipeline Branching
            # Branch A: Educational Deflections (Advisory / Comparison / Out of Scope)
            if intent in ("ADVISORY", "COMPARATIVE", "OUT_OF_SCOPE"):
                answer = MFRefusalHandler.get_refusal_response(intent)
                latency = (time.perf_counter() - start_time) * 1000
                return {
                    "answer": answer,
                    "source_url": None,
                    "intent": intent,
                    "last_updated": None,
                    "latency_ms": round(latency, 2),
                }

            # Branch B: Performance Calculation Deflection (Factsheet redirect)
            elif intent == "PERFORMANCE_CALC":
                # First retrieve chunks to extract recent fetch dates if available for the footer
                chunks = []
                try:
                    chunks = retrieve(sanitized_query, top_k=3, scheme_hint=sanitized_query)
                except Exception as e:
                    logger.warning(f"Pre-retrieval fetch for performance date calculation failed: {e}")

                answer, citation_url = MFPerformanceHandler.generate_performance_response(
                    query=sanitized_query,
                    retrieved_chunks=chunks,
                )
                
                # Extract date from footer for metadata separation
                date_match = re.search(r"Last updated from sources:\s*(\d{4}-\d{2}-\d{2})", answer)
                last_updated = date_match.group(1) if date_match else "2026-05-18"

                latency = (time.perf_counter() - start_time) * 1000
                return {
                    "answer": answer,
                    "source_url": citation_url,
                    "intent": "PERFORMANCE_CALC",
                    "last_updated": last_updated,
                    "latency_ms": round(latency, 2),
                }

            # Branch C: Factual RAG Q&A Pipeline
            else:
                # Execute vector store search
                logger.info(f"Query {query_hash}: Initiating semantic context search.")
                chunks = retrieve(sanitized_query, top_k=3, scheme_hint=sanitized_query)
                
                if not chunks:
                    logger.warning(f"Query {query_hash}: Vector store returned zero matching context chunks.")
                    latency = (time.perf_counter() - start_time) * 1000
                    return {
                        "answer": "I couldn't find this information in the approved sources.",
                        "source_url": None,
                        "intent": "FACTUAL",
                        "last_updated": None,
                        "latency_ms": round(latency, 2),
                    }

                # Run constrained generator
                answer, citation_url = MFGenerator.generate_factual_response(
                    query=sanitized_query,
                    retrieved_chunks=chunks,
                )

                # Extract max freshness date from active chunks
                dates = []
                for c in chunks:
                    date_val = c.get("metadata", {}).get("last_fetched_at")
                    if date_val:
                        match = re.search(r"\d{4}-\d{2}-\d{2}", date_val)
                        if match:
                            dates.append(match.group(0))
                last_updated = max(dates) if dates else "2026-05-18"

                latency = (time.perf_counter() - start_time) * 1000
                return {
                    "answer": answer,
                    "source_url": citation_url,
                    "intent": "FACTUAL",
                    "last_updated": last_updated,
                    "latency_ms": round(latency, 2),
                }

        except Exception as e:
            logger.error(f"E2E Pipeline execution error for query {query_hash}: {e}", exc_info=True)
            latency = (time.perf_counter() - start_time) * 1000
            return {
                "answer": "An unexpected error occurred. Please try again later.",
                "source_url": None,
                "intent": "ERROR",
                "last_updated": None,
                "latency_ms": round(latency, 2),
            }
