"""Phase 3.5 — Metadata-Aware Retrieval Filtering.

Provides inventory matching and scheme hint routing filters to isolate searches to specific schemes.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("retrieval.filter")

__all__ = ["find_matching_slugs"]


def find_matching_slugs(scheme_hint: str) -> list[str]:
    """Search inventory to find slugs matching the given scheme name or slug hint."""
    hint = scheme_hint.strip().lower()
    if not hint:
        return []

    try:
        from src.corpus.inventory import load_inventory
        entries = load_inventory()
    except Exception as e:
        logger.warning(f"Could not load inventory for scheme_hint matching: {e}")
        return []

    # Common term mappings for fuzzy matching
    term_mappings = {
        "nifty50": "nifty 50",
        "nifty 50": "nifty 50",
        "nifty50index": "nifty 50 index",
        "niftyindex": "nifty index",
        "largecap": "large cap",
        "midcap": "mid cap",
        "smallcap": "small cap",
        "flexicap": "flexi cap",
        "multicap": "multi cap",
        "prudential": "prudential",
    }

    # Normalize hint using term mappings
    normalized_hint = hint
    for variant, standard in term_mappings.items():
        normalized_hint = normalized_hint.replace(variant, standard)

    # Extract key terms from hint for scoring
    hint_terms = set(normalized_hint.split())
    
    scored_matches: list[tuple[str, float]] = []
    
    for entry in entries:
        # Check AMC listing match
        if entry.source_type == "amc_listing":
            if "amc" in hint or "listing" in hint or "screener" in hint:
                scored_matches.append(("", 1.0))
                continue
        
        # Check scheme slug match
        if entry.scheme_slug:
            slug_lower = entry.scheme_slug.lower()
            # Exact match - highest score
            if hint == slug_lower:
                scored_matches.append((entry.scheme_slug, 1.0))
                continue
            
            # Check scheme name exact match
            if entry.scheme_name:
                name_lower = entry.scheme_name.lower()
                if hint == name_lower:
                    scored_matches.append((entry.scheme_slug, 1.0))
                    continue
                
                # Extract terms from scheme name for scoring
                name_terms = set(name_lower.split())
                
                # Calculate overlap score
                overlap = len(hint_terms & name_terms)
                hint_coverage = overlap / len(hint_terms) if hint_terms else 0
                name_coverage = overlap / len(name_terms) if name_terms else 0
                
                # Score based on term overlap
                score = (hint_coverage * 0.6) + (name_coverage * 0.4)
                
                # Boost score if hint is a substring
                if hint in name_lower or name_lower in hint:
                    score += 0.2
                
                # Boost score if normalized hint matches
                if normalized_hint in name_lower or name_lower in normalized_hint:
                    score += 0.1
                
                # Only include if score is above threshold
                if score >= 0.3:
                    scored_matches.append((entry.scheme_slug, score))
                    continue

    # Sort by score and return top matches
    scored_matches.sort(key=lambda x: x[1], reverse=True)
    
    # Return all matches with score >= 0.7 (more selective threshold)
    high_score_matches = [slug for slug, score in scored_matches if score >= 0.7]
    if high_score_matches:
        return list(set(high_score_matches))
    
    # Return top 2 matches if no high scores (more restrictive)
    if scored_matches:
        return list(set([slug for slug, score in scored_matches[:2]]))
    
    return []
