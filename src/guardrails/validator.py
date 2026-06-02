"""Phase 4.3 — Post-Generation Response Validator.

Inspects generated LLM answers to guarantee strict sentence count constraints,
single approved citation URLs, absence of advisory language, and data freshness footers.
"""

from __future__ import annotations

import logging
import re
from typing import Any

from src.corpus.inventory import allowed_url_set
from src.guardrails.refusal import MFRefusalHandler

logger = logging.getLogger("guardrails.validator")

__all__ = ["MFResponseValidator"]

ADVISORY_PATTERN = re.compile(
    r"\b(?:should invest|recommend|suggest|better choice|best option|is a good buy|good investment|safe to invest)\b",
    re.IGNORECASE,
)


class MFResponseValidator:
    """Post-generation compliance checker verifying and fixing sentence counts, citations, and advisory terms."""

    @classmethod
    def clean_sentence_count(cls, text: str) -> str:
        """Truncate answer cleanly to maximum of 3 sentences if LLM exceeded bounds.

        Uses regex lookbehinds to avoid split false-positives on decimal dots or currency tokens.
        """
        # Split on period followed by space/uppercase/end of string, ignoring common abbreviations
        sentence_end = re.compile(r"(?<!\bRs)(?<!\bNo)(?<!\bVol)(?<!\bNAV)(?<!\betc)\.(?=\s+[A-Z]|\s*$)", re.MULTILINE)
        raw_sentences = sentence_end.split(text.strip())
        
        sentences = [s.strip() for s in raw_sentences if s.strip()]
        if len(sentences) <= 3:
            return text.strip()

        logger.warning(f"Response exceeded 3 sentences ({len(sentences)}). Truncating to 3.")
        truncated = ". ".join(sentences[:3])
        if not truncated.endswith("."):
            truncated += "."
        return truncated

    @classmethod
    def extract_urls(cls, text: str) -> list[str]:
        """Extract all http/https urls from a text string, stripping trailing punctuation."""
        raw_urls = re.findall(r"https?://[^\s()\"']+", text)
        cleaned = []
        for u in raw_urls:
            cleaned.append(u.rstrip(".,;:!?"))
        return cleaned

    @classmethod
    def enforce_citation_constraint(cls, text: str, fallback_url: str) -> tuple[str, str]:
        """Verify that exactly one URL is present, and that it is in the closed 30-URL inventory.

        Returns:
            A tuple of (fixed_text, resolved_citation_url).
        """
        raw_urls = re.findall(r"https?://[^\s()\"']+", text)
        approved_urls = allowed_url_set()

        url_info = []
        for raw in raw_urls:
            cleaned = raw.rstrip(".,;:!?")
            is_app = (cleaned.strip().rstrip("/") in approved_urls) or (cleaned.strip() in approved_urls)
            url_info.append((raw, cleaned, is_app))

        approved_info = [info for info in url_info if info[2]]

        cleaned_text = text

        if not approved_info:
            logger.warning("No valid closed-corpus URL found in generation. Attaching top context URL.")
            # Remove any unapproved links that might have been generated
            for raw, _, _ in url_info:
                cleaned_text = cleaned_text.replace(raw, "")
            
            # Clean up double spaces from replacements
            cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
            
            # Append citation cleanly
            if not cleaned_text.endswith("."):
                cleaned_text += "."
            cleaned_text += f" Source: {fallback_url}"
            return cleaned_text, fallback_url

        # Select the first approved URL as primary
        primary_raw, primary_cleaned, _ = approved_info[0]
        trailing_punctuation = primary_raw[len(primary_cleaned):]

        # Replace all other raw URLs with empty string, and replace primary raw with primary cleaned + trailing punctuation
        for raw, cleaned, is_app in url_info:
            if raw == primary_raw:
                cleaned_text = cleaned_text.replace(primary_raw, primary_cleaned + trailing_punctuation, 1)
            else:
                cleaned_text = cleaned_text.replace(raw, "")

        cleaned_text = re.sub(r"\s+", " ", cleaned_text).strip()
        return cleaned_text, primary_cleaned

    @classmethod
    def contains_advisory_language(cls, text: str) -> bool:
        """Spot check output text for non-compliant financial advisor expressions."""
        return bool(ADVISORY_PATTERN.search(text))

    @classmethod
    def validate_and_fix(
        cls,
        text: str,
        retrieved_chunks: list[dict[str, Any]],
        fallback_url: str,
    ) -> tuple[str, str | None, bool]:
        """Run all compliance checks. If possible, auto-heals output; otherwise flags failure.

        Args:
            text: Raw generated output from the LLM.
            retrieved_chunks: Active context chunks from retrieval.
            fallback_url: The primary retrieved source_url to use as fallback.

        Returns:
            A tuple containing:
                - fixed_text (str): Compliant generated answer or refusal.
                - citation_url (str | None): Validated single citation URL (or None if refusal/PII).
                - is_valid (bool): True if passed compliance checks or successfully auto-healed.
        """
        cleaned_text = text.strip()

        # 1. Advisory Sweep
        if cls.contains_advisory_language(cleaned_text):
            logger.warning("Advisory words detected in generated output. Deflecting to refusal template.")
            refusal_msg = MFRefusalHandler.get_refusal_response("ADVISORY")
            return refusal_msg, None, False

        # 2. Clean Sentence Count (Max 3)
        cleaned_text = cls.clean_sentence_count(cleaned_text)

        # 3. Citation Check (Exactly 1 URL in closed inventory)
        cleaned_text, citation_url = cls.enforce_citation_constraint(cleaned_text, fallback_url)

        # 4. Freshness Footer Date Check
        # Footer Date = max(last_fetched_at) of chunks used in generation
        dates: list[str] = []
        for chunk in retrieved_chunks:
            meta = chunk.get("metadata", {})
            date_val = meta.get("last_fetched_at")
            if date_val:
                # Match YYYY-MM-DD format
                match = re.search(r"\d{4}-\d{2}-\d{2}", date_val)
                if match:
                    dates.append(match.group(0))

        footer_date = max(dates) if dates else "2026-05-18"
        footer_line = f"Last updated from sources: {footer_date}"

        # Strip any existing footer to avoid duplicates
        cleaned_text = re.sub(r"Last updated from sources: \d{4}-\d{2}-\d{2}", "", cleaned_text).strip()
        
        # Attach footer cleanly
        if not cleaned_text.endswith("."):
            cleaned_text += "."
        cleaned_text = f"{cleaned_text}\n{footer_line}"

        return cleaned_text, citation_url, True
