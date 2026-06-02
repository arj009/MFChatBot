"""Phase 4.2 — Refusal Handler.

Manages dynamic formatting and delivery of refusal, deflection, and block responses
for non-factual or compliance-violating user inputs.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar

import yaml

logger = logging.getLogger("guardrails.refusal")

__all__ = ["MFRefusalHandler"]

PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_PATH = PROJECT_ROOT / "config" / "refusal_templates.yaml"
LINKS_PATH = PROJECT_ROOT / "config" / "educational_links.yaml"

DEFAULT_EDUCATIONAL_URL = "https://www.amfiindia.com/investor/knowledge-center-info?zoneName=IntroductionMutualFunds"
DEFAULT_EDUCATIONAL_LABEL = "AMFI — Mutual Fund investor information"


class MFRefusalHandler:
    """Loads refusal templates and educational links from configs and generates formatted deflection messages."""

    _templates: ClassVar[dict[str, str] | None] = None
    _educational_link: ClassVar[str | None] = None

    @classmethod
    def load_configs(cls) -> None:
        """Lazy-load yaml refusal configurations into memory."""
        if cls._templates is not None:
            return

        # 1. Load refusal templates
        try:
            with TEMPLATES_PATH.open(encoding="utf-8") as f:
                data = yaml.safe_load(f)
                cls._templates = data.get("templates", {})
                logger.info(f"Loaded {len(cls._templates)} refusal templates from '{TEMPLATES_PATH.name}'.")
        except Exception as e:
            logger.error(f"Failed to load refusal templates: {e}. Using fallback copies.")
            cls._templates = {}

        # 2. Load educational links and construct standard markdown link
        try:
            with LINKS_PATH.open(encoding="utf-8") as f:
                links = yaml.safe_load(f)
                default_link = links.get("default", {})
                label = default_link.get("label", DEFAULT_EDUCATIONAL_LABEL)
                url = default_link.get("url", DEFAULT_EDUCATIONAL_URL)
                cls._educational_link = f"[{label}]({url})"
        except Exception as e:
            logger.error(f"Failed to load educational links: {e}. Using fallback AMFI link.")
            cls._educational_link = f"[{DEFAULT_EDUCATIONAL_LABEL}]({DEFAULT_EDUCATIONAL_URL})"

    @classmethod
    def get_refusal_response(
        cls,
        intent: str,
        scheme_link: str | None = None,
        date: str | None = None,
    ) -> str:
        """Retrieve and format a compliant deflection response for a given non-factual intent.

        Args:
            intent: The query intent classification label (e.g. ADVISORY, COMPARATIVE, OUT_OF_SCOPE, PII_RISK, PERFORMANCE_CALC).
            scheme_link: Optional Groww URL to include in performance calculation templates.
            date: Optional last updated date for performance footer (default to today's date if missing).

        Returns:
            A clean, formatted text response string.
        """
        cls.load_configs()
        
        intent_key = intent.lower()
        template = cls._templates.get(intent_key) if cls._templates else None

        # Fallback raw templates in case loading failed
        if not template:
            if intent_key == "advisory":
                template = "I can only share factual details, not personal investment advice. general investor education: {educational_link}"
            elif intent_key == "comparative":
                template = "I can't compare funds—that would be investment advice. Learn more: {educational_link}"
            elif intent_key == "pii_risk":
                template = "Please don’t share personal identifiers such as PAN, Aadhaar, account numbers, or OTPs here."
            elif intent_key == "performance_calc":
                template = "I can’t project returns. Performance details are on the Groww page: {scheme_link}\nLast updated from sources: {date}"
            else:
                template = "That question isn’t covered by my facts-only corpus. Learn more: {educational_link}"

        # Format placeholders based on the template requirements
        educational_link = cls._educational_link or f"[{DEFAULT_EDUCATIONAL_LABEL}]({DEFAULT_EDUCATIONAL_URL})"
        
        try:
            # 1. PII risk has no placeholders (Strictly NO URLs/Links in response)
            if intent_key == "pii_risk":
                return template.strip()

            # 2. Performance calc requires scheme link and date footer
            if intent_key == "performance_calc":
                resolved_link = scheme_link or "https://groww.in/mutual-funds/filter?fund_house=%5B%22ICICI+Prudential+Mutual+Fund%22%5D"
                resolved_date = date or "2026-05-18"
                return template.format(scheme_link=resolved_link, date=resolved_date).strip()

            # 3. Standard refusals require educational link
            return template.format(educational_link=educational_link).strip()

        except Exception as e:
            logger.error(f"Failed to format refusal template for '{intent}': {e}")
            # Safe basic string fallback on formatting failure
            if intent_key == "pii_risk":
                return "Please don’t share personal details. This assistant does not collect personal info."
            return "I am not able to answer this type of question. Please refer to AMFI or SEBI official pages for guidance."
