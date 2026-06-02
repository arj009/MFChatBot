"""Phase 4.3 — Constrained LLM Generator.

Coordinates query vector context retrieval, system prompt formatting, Groq API interaction,
and post-generation validation to output strict factual answers.
"""

from __future__ import annotations

import logging
import os
import re
from typing import Any, ClassVar

from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv(override=True)

from src.generation.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.guardrails.validator import MFResponseValidator

logger = logging.getLogger("generation.generator")

__all__ = ["MFGenerator"]

DEFAULT_MODEL = "llama-3.3-70b-versatile"


class MFGenerator:
    """Orchestrates compliant LLM generation, sending queries to Groq and running validators."""

    _client: ClassVar[Groq | None] = None

    @classmethod
    def get_groq_client(cls) -> Groq:
        """Initialize and return the Groq client singleton using environment variables."""
        if cls._client is None:
            api_key = os.environ.get("GROQ_API_KEY")
            cls._client = Groq(api_key=api_key or "MOCK_KEY")
        return cls._client

    @classmethod
    def generate_factual_response(
        cls,
        query: str,
        retrieved_chunks: list[dict[str, Any]],
        model: str | None = None,
    ) -> tuple[str, str | None]:
        """Synthesize a factual, objective 3-sentence answer strictly based on retrieval context.

        Args:
            query: The user search question.
            retrieved_chunks: A list of retrieved context chunk dictionaries from the vector DB.
            model: Optional Groq model identifier (defaults to llama3-70b-8192).

        Returns:
            A tuple of (validated_answer_text, citation_url).
        """
        if not retrieved_chunks:
            logger.warning("Empty context chunks received. Deflecting to unknown answer.")
            return "I couldn't find this information in the approved sources.", None

        fallback_url = retrieved_chunks[0]["metadata"].get("source_url") or "https://groww.in/mutual-funds/filter?fund_house=%5B%22ICICI+Prudential+Mutual+Fund%22%5D"

        # 1. Check GROQ API Availability
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key or api_key == "MOCK_KEY":
            logger.info("GROQ_API_KEY not configured. Invoking high-quality offline extraction fallback.")
            
            # Extract first 2 sentences from the top semantic hit to simulate factual LLM response
            top_text = retrieved_chunks[0].get("text", "")
            sentence_end = re.compile(r"(?<!\bRs)(?<!\bNo)(?<!\bVol)(?<!\bNAV)(?<!\betc)\.(?=\s+[A-Z]|\s*$)")
            raw_sentences = [s.strip() for s in sentence_end.split(top_text) if s.strip()]
            
            simulated_answer = ". ".join(raw_sentences[:2])
            if simulated_answer and not simulated_answer.endswith("."):
                simulated_answer += "."
            
            # Let post-generation validator format, check URLs, and attach footer
            fixed_text, citation_url, _ = MFResponseValidator.validate_and_fix(
                text=simulated_answer,
                retrieved_chunks=retrieved_chunks,
                fallback_url=fallback_url,
            )
            return fixed_text, citation_url

        # 2. Compile context block
        context_parts: list[str] = []
        for idx, chunk in enumerate(retrieved_chunks):
            source = chunk["metadata"].get("source_url", "unknown")
            text = chunk.get("text", "")
            context_parts.append(f"Chunk {idx} (source_url: {source}):\n{text}\n")
        context_text = "\n".join(context_parts)

        # 3. Format prompt template
        user_prompt = USER_PROMPT_TEMPLATE.format(query=query, context_text=context_text)
        selected_model = model or os.environ.get("GROQ_GENERATOR_MODEL", DEFAULT_MODEL)

        # Retries loop (maximum 2 LLM execution attempts)
        for attempt in range(1, 3):
            try:
                client = cls.get_groq_client()
                response = client.chat.completions.create(
                    model=selected_model,
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=0.0,  # Zero temperature forces reproducibility and deters hallucination
                    max_tokens=200,
                )

                raw_output = response.choices[0].message.content.strip()
                logger.info(f"LLM Generation Attempt {attempt}: Received raw output.")

                # Run post-generation validator
                fixed_text, citation_url, is_valid = MFResponseValidator.validate_and_fix(
                    text=raw_output,
                    retrieved_chunks=retrieved_chunks,
                    fallback_url=fallback_url,
                )

                if is_valid:
                    return fixed_text, citation_url

                # If validator flagged a violation, retry with low temperature
                logger.warning(f"Generation Attempt {attempt} failed validator checks. Retrying...")

            except Exception as e:
                logger.error(f"Groq generation error on attempt {attempt}: {e}")

        # If LLM generation and retries fail, return safely formatted top chunk snippet
        logger.warning("Factual LLM generation exhausted all retries. Returning safe fallback.")
        top_text = retrieved_chunks[0].get("text", "")
        sentence_end = re.compile(r"(?<!\bRs)(?<!\bNo)(?<!\bVol)(?<!\bNAV)(?<!\betc)\.(?=\s+[A-Z]|\s*$)")
        raw_sentences = [s.strip() for s in sentence_end.split(top_text) if s.strip()]
        fallback_msg = ". ".join(raw_sentences[:2])
        if fallback_msg and not fallback_msg.endswith("."):
            fallback_msg += "."
            
        fixed_text, citation_url, _ = MFResponseValidator.validate_and_fix(
            text=fallback_msg,
            retrieved_chunks=retrieved_chunks,
            fallback_url=fallback_url,
        )
        return fixed_text, citation_url
