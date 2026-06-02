"""Phase 4.4 — Performance-Query Path.

Intercepts performance and projections queries, resolves target schemes, and returns
compliant deflection answers containing Groww links instead of numeric computations.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.corpus.inventory import load_inventory
from src.guardrails.refusal import MFRefusalHandler

logger = logging.getLogger("generation.performance")

__all__ = ["MFPerformanceHandler"]

DEFAULT_LISTING_URL = "https://groww.in/mutual-funds/filter?fund_house=%5B%22ICICI+Prudential+Mutual+Fund%22%5D"


class MFPerformanceHandler:
    """Resolves target mutual funds for performance queries and yields compliant deflection templates."""

    @classmethod
    def resolve_scheme_url(cls, query: str) -> str:
        """Analyze query to fuzzy-match and retrieve the exact Groww url of the target scheme."""
        try:
            entries = load_inventory()
            cleaned_query = query.lower()
            # Split into individual lowercase alphanumeric tokens for exact word matching
            query_tokens = set(re.split(r"[^\w]+", cleaned_query))
            
            best_entry = None
            best_score = 0
            
            # Common mutual fund keywords that are too generic to distinguish specific schemes
            stop_words = {"icici", "prudential", "mutual", "fund", "direct", "growth", "scheme", "plan", "equity", "debt"}
            
            for entry in entries:
                if entry.source_type == "amc_listing":
                    continue
                
                score = 0
                # 1. Match against individual unique words in the slug
                if entry.scheme_slug:
                    slug_parts = entry.scheme_slug.split("-")
                    unique_slug_kws = [w for w in slug_parts if w not in stop_words and len(w) > 2]
                    for kw in unique_slug_kws:
                        if kw in query_tokens:
                            score += 10  # Assign high weight to unique slug identifiers
                
                # 2. Match against individual unique words in the official name
                if entry.scheme_name:
                    name_words = re.split(r"[^\w]+", entry.scheme_name.lower())
                    unique_name_kws = [w for w in name_words if w not in stop_words and len(w) > 2]
                    for kw in unique_name_kws:
                        if kw in query_tokens:
                            score += 5  # Secondary weight to official name keywords
                
                if score > best_score:
                    best_score = score
                    best_entry = entry
            
            if best_entry and best_score > 0:
                logger.info(f"Performance resolver: Matched scheme '{best_entry.scheme_name}' (score={best_score})")
                return best_entry.url
                
        except Exception as e:
            logger.warning(f"Failed to fuzzy-resolve scheme URL for performance: {e}")

        logger.info("Performance resolver: No specific scheme resolved. Defaulting to AMC listing.")
        return DEFAULT_LISTING_URL

    @classmethod
    def generate_performance_response(
        cls,
        query: str,
        retrieved_chunks: list[dict[str, Any]] | None = None,
    ) -> tuple[str, str]:
        """Produce a compliant performance deflection response.

        Args:
            query: The user input query string.
            retrieved_chunks: Optional semantic retrieval hits to extract recent fetch dates.

        Returns:
            A tuple of:
                - response_text (str): Compliant one-sentence template.
                - citation_url (str): Exact Groww citation link matching the target scheme.
        """
        # 1. Resolve matching scheme URL
        citation_url = cls.resolve_scheme_url(query)

        # 2. Extract data freshness date
        dates: list[str] = []
        if retrieved_chunks:
            for chunk in retrieved_chunks:
                meta = chunk.get("metadata", {})
                date_val = meta.get("last_fetched_at")
                if date_val:
                    match = re.search(r"\d{4}-\d{2}-\d{2}", date_val)
                    if match:
                        dates.append(match.group(0))

        # Default to standard inventory review date if no chunks or fetch dates exist
        last_updated_date = max(dates) if dates else "2026-05-18"

        # 3. Retrieve formatted response template
        response_text = MFRefusalHandler.get_refusal_response(
            intent="PERFORMANCE_CALC",
            scheme_link=citation_url,
            date=last_updated_date,
        )

        return response_text, citation_url
