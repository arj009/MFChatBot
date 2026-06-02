"""Phase 4.1 — Query Classifier.

Categorizes user queries into FACTUAL, ADVISORY, COMPARATIVE, PERFORMANCE_CALC,
OUT_OF_SCOPE, or PII_RISK intents using a hybrid Regex-LLM approach.
"""

from __future__ import annotations

import logging
import os
import re
from typing import ClassVar

from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv(override=True)

logger = logging.getLogger("guardrails.classifier")

__all__ = ["MFQueryClassifier"]

DEFAULT_MODEL = "llama-3.1-8b-instant"


class MFQueryClassifier:
    """Hybrid classifier utilizing Regex for security sweeps (PII) and Groq LLM for intent routing."""

    _client: ClassVar[Groq | None] = None

    @classmethod
    def get_groq_client(cls) -> Groq:
        """Initialize and return the Groq client singleton using environment variables."""
        if cls._client is None:
            api_key = os.environ.get("GROQ_API_KEY")
            if not api_key:
                logger.warning("GROQ_API_KEY environment variable is not set. Classification may rely on fallback modes.")
            cls._client = Groq(api_key=api_key or "MOCK_KEY")
        return cls._client

    @classmethod
    def detect_pii_risk(cls, text: str) -> bool:
        """Run standard fast regex checks to identify PII (PAN, Aadhaar, phone, email, OTP)."""
        # 1. Aadhaar: 12 digits (with optional spaces or hyphens)
        aadhaar_pattern = re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}\b")
        
        # 2. PAN Card: 5 uppercase letters + 4 digits + 1 uppercase letter
        pan_pattern = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b", re.IGNORECASE)
        
        # 3. Email: Standard email pattern
        email_pattern = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b")
        
        # 4. Indian Mobile Phone Number: +91 or 0 prefix, followed by 10 digits starting with 6-9
        phone_pattern = re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b")
        
        # 5. OTP Check: 4 to 6 digit numbers in close context to keyword "otp" or "code"
        otp_digits = re.compile(r"\b\d{4,6}\b")
        otp_context = re.compile(r"(?:otp|one[- ]time[- ]password|code|verification|verify)", re.IGNORECASE)

        if aadhaar_pattern.search(text):
            logger.info("PII Blocked: Aadhaar pattern detected.")
            return True
        if pan_pattern.search(text):
            logger.info("PII Blocked: PAN Card pattern detected.")
            return True
        if email_pattern.search(text):
            logger.info("PII Blocked: Email address detected.")
            return True
        if phone_pattern.search(text):
            logger.info("PII Blocked: Phone number detected.")
            return True
        if otp_digits.search(text) and otp_context.search(text):
            logger.info("PII Blocked: OTP verification pattern detected.")
            return True

        return False

    @classmethod
    def fallback_classify(cls, text: str) -> str:
        """Provide a rule-based fallback classification when GROQ API key is missing or offline."""
        cleaned = text.strip().lower()
        
        # 1. Performance calculation cues
        perf_keywords = ["grow to", "cagr", "returns of", "project", "historical return", "future value", "invested 10k", "what will 10000 become"]
        if any(kw in cleaned for kw in perf_keywords):
            return "PERFORMANCE_CALC"
        
        # 2. Comparative cues
        comp_keywords = ["better than", "vs", "compared to", "which fund is better", "comparison", "best of the two", "better choice"]
        if any(kw in cleaned for kw in comp_keywords):
            return "COMPARATIVE"

        # 3. Advisory cues
        advisory_keywords = ["should i invest", "recommend", "best fund for me", "is it safe to invest", "financial advice", "suggest a fund", "good investment"]
        if any(kw in cleaned for kw in advisory_keywords):
            return "ADVISORY"

        # 4. Out of scope cues (highly generic chit chat or external companies)
        out_scope_keywords = ["weather", "hello", "hi", "how are you", "joke", "stock market", "reliance", "tata", "hDFC"]
        if any(kw in cleaned for kw in out_scope_keywords) and not any(k in cleaned for k in ["icici", "prudential", "ratio", "load", "sip"]):
            return "OUT_OF_SCOPE"

        # Default to FACTUAL for unknown queries so retrieval can try its best
        return "FACTUAL"

    @classmethod
    def classify(cls, query: str) -> str:
        """Classify user query intent, returning FACTUAL, ADVISORY, COMPARATIVE, PERFORMANCE_CALC, OUT_OF_SCOPE, or PII_RISK.

        Args:
            query: The user input query string.

        Returns:
            The raw label string.
        """
        query_str = query.strip()
        if not query_str:
            return "OUT_OF_SCOPE"

        # 1. PII Risk Sweep (Strict Regex) - Prevents PII from ever being sent to third-party LLMs
        if cls.detect_pii_risk(query_str):
            return "PII_RISK"

        # 2. Check GROQ Availability
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "MOCK_KEY":
            logger.info("Using local rule-based fallback classifier (no GROQ_API_KEY found).")
            return cls.fallback_classify(query_str)

        # 3. Groq LLM Intent Classifier
        try:
            client = cls.get_groq_client()
            model = os.environ.get("GROQ_CLASSIFIER_MODEL", DEFAULT_MODEL)

            system_prompt = (
                "You are a strict, objective intent classifier for a facts-only mutual fund Q&A assistant.\n"
                "Your task is to classify the user's input query into EXACTLY one of the following labels:\n\n"
                "1. `FACTUAL`: Factual questions about a specific mutual fund scheme's parameters, e.g. expense ratio, exit load, minimum investment, fund manager, benchmark, category, NAV, riskometer.\n"
                "2. `ADVISORY`: Queries asking for financial, investment, or personal planning advice, e.g. 'Should I invest?', 'Is this good for long term?', 'How much should I invest?', 'Suggest a good fund for retirement'.\n"
                "3. `COMPARATIVE`: Queries comparing two or more schemes, or asking which one is 'better', 'best', e.g. 'Which fund is better?', 'Fund A vs Fund B'.\n"
                "4. `PERFORMANCE_CALC`: Queries asking to project returns, calculate future growth, or calculate CAGR/numeric performance outcomes, e.g. 'What will 10k grow to in 5 years?', 'What is the return on 5000 investment?'.\n"
                "5. `OUT_OF_SCOPE`: Queries about general topics, other companies, chit-chat, general news, or anything unrelated to factual details of ICICI Prudential schemes.\n\n"
                "Your response must contain ONLY the raw label name in uppercase (no extra words, no explanation, no formatting, no markdown): either FACTUAL, ADVISORY, COMPARATIVE, PERFORMANCE_CALC, or OUT_OF_SCOPE."
            )

            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query_str},
                ],
                temperature=0.0,
                max_tokens=10,
            )

            raw_label = response.choices[0].message.content.strip().upper()
            
            # Clean output if the model added punctuation or markdown
            cleaned_label = re.sub(r"[^A-Z_]", "", raw_label)
            
            valid_labels = {"FACTUAL", "ADVISORY", "COMPARATIVE", "PERFORMANCE_CALC", "OUT_OF_SCOPE"}
            if cleaned_label in valid_labels:
                logger.info(f"GROQ Classification: '{cleaned_label}' for query '{query_str[:30]}...'")
                return cleaned_label

            logger.warning(f"Unexpected label returned from GROQ: '{raw_label}'. Invoking fallback.")
            return cls.fallback_classify(query_str)

        except Exception as e:
            logger.error(f"GROQ classification failed: {e}. Falling back to rule-based logic.")
            return cls.fallback_classify(query_str)
