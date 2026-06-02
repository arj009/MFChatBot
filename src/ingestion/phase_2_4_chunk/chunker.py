"""Phase 2.4 — Chunking normalized documents by Markdown heading sections."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.corpus.inventory import AMC_NAME, CorpusEntry, load_inventory
from src.ingestion.phase_2_1_fetch import raw_meta_path
from src.ingestion.phase_2_2_parse import parsed_json_path
from src.ingestion.phase_2_3_normalize import normalized_json_path
from src.ingestion.shared.paths import NORMALIZED_DIR, PARSED_DIR, RAW_DIR

__all__ = [
    "chunk_all",
    "chunk_entry",
    "validate_phase2_4",
]

MAX_CHUNKS = 5
TARGET_TOKENS = 600
OVERLAP = 0.1


def _split_by_token_window(text: str) -> list[str]:
    """Split text into overlapping chunks of approx 600 words/tokens."""
    words = text.split()
    if not words:
        return []
    chunk_size = TARGET_TOKENS
    step = int(chunk_size * (1 - OVERLAP))
    return [" ".join(words[i : i + chunk_size]) for i in range(0, len(words), step)]


def chunk_entry(
    entry: CorpusEntry,
    normalized_text: str,
    document_title: str,
    last_fetched_at: str,
    content_hash: str,
) -> list[dict[str, Any]]:
    """Split normalized text into section-based chunks with full metadata context."""
    lines = normalized_text.splitlines()
    if not lines:
        return []

    # The first line of normalized text is always the main title ("# Title")
    title_line = lines[0] if lines[0].startswith("# ") else f"# {document_title}"

    sections: list[tuple[str, str]] = []
    current_heading = ""
    current_body_lines: list[str] = []

    # Iterate lines starting from index 1 (after the title line)
    for line in lines[1:]:
        if line.startswith("## "):
            # Save previous section if it had content or a heading
            body_text = "\n".join(current_body_lines).strip()
            if current_heading or body_text:
                sections.append((current_heading, body_text))
            current_heading = line
            current_body_lines = []
        else:
            current_body_lines.append(line)

    # Save the last section
    body_text = "\n".join(current_body_lines).strip()
    if current_heading or body_text:
        sections.append((current_heading, body_text))

    # Fallback to token window if no markdown sections found
    if not sections:
        section_texts = _split_by_token_window("\n".join(lines[1:]))
        sections = [("", t) for t in section_texts]
    elif len(sections) > MAX_CHUNKS:
        # Merge sections
        merged_sections: list[tuple[str, str]] = []
        current_words: list[str] = []
        for h, b in sections:
            current_words.extend((h + " " + b).split())
            if len(current_words) >= TARGET_TOKENS:
                merged_sections.append(("", " ".join(current_words)))
                current_words = []
        if current_words:
            merged_sections.append(("", " ".join(current_words)))
        sections = merged_sections

    chunks: list[dict[str, Any]] = []
    
    # Extract and prioritize Key facts section for better retrieval of factual queries
    key_facts_chunk = None
    other_sections = []
    
    for heading, body in sections:
        if "key facts" in heading.lower():
            # Create a dedicated key facts chunk with enhanced context for better retrieval
            # Add query-relevant keywords to boost semantic matching
            enhanced_body = body
            if entry.scheme_name:
                # Add scheme name in different forms for better matching
                enhanced_body = f"{enhanced_body}\n\nScheme: {entry.scheme_name}"
            parts = [title_line, heading, enhanced_body]
            chunk_text = "\n\n".join(parts).strip()
            key_facts_chunk = {
                "source_url": entry.url,
                "source_type": entry.source_type,
                "amc": AMC_NAME,
                "scheme_name": entry.scheme_name if entry.source_type == "scheme_page" else None,
                "scheme_slug": entry.scheme_slug,
                "scheme_category": entry.category if entry.source_type == "scheme_page" else None,
                "document_title": document_title,
                "last_fetched_at": last_fetched_at,
                "content_hash": content_hash,
                "chunk_index": 0,
                "text": chunk_text,
            }
        else:
            other_sections.append((heading, body))
    
    # Add key facts chunk first if it exists (highest priority for retrieval)
    chunk_idx = 0
    if key_facts_chunk:
        chunks.append(key_facts_chunk)
        chunk_idx += 1
    
    # Add other sections
    for heading, body in other_sections:
        # Format the text of the chunk: [Document Title]\n\n[Section Heading]\n[Section Body]
        parts = [title_line]
        if heading:
            parts.append(heading)
        if body:
            parts.append(body)
        chunk_text = "\n\n".join(parts).strip()

        chunks.append({
            "source_url": entry.url,
            "source_type": entry.source_type,
            "amc": AMC_NAME,
            "scheme_name": entry.scheme_name if entry.source_type == "scheme_page" else None,
            "scheme_slug": entry.scheme_slug,
            "scheme_category": entry.category if entry.source_type == "scheme_page" else None,
            "document_title": document_title,
            "last_fetched_at": last_fetched_at,
            "content_hash": content_hash,
            "chunk_index": chunk_idx,
            "text": chunk_text,
        })
        chunk_idx += 1

    return chunks


def chunk_all(
    *,
    raw_dir: Path | None = None,
    parsed_dir: Path | None = None,
    normalized_dir: Path | None = None,
) -> list[dict[str, Any]]:
    """Load normalized JSON files, extract metadata, and chunk all documents."""
    entries = load_inventory()
    all_chunks: list[dict[str, Any]] = []

    for entry in sorted(entries, key=lambda e: e.id):
        norm_path = normalized_json_path(entry, normalized_dir or NORMALIZED_DIR)
        parsed_path = parsed_json_path(entry, parsed_dir or PARSED_DIR)
        meta_path = raw_meta_path(entry, raw_dir or RAW_DIR)

        if not norm_path.is_file():
            raise FileNotFoundError(f"Missing normalized file: {norm_path}. Run Phase 2.3 first.")
        if not parsed_path.is_file():
            raise FileNotFoundError(f"Missing parsed file: {parsed_path}. Run Phase 2.2 first.")
        if not meta_path.is_file():
            raise FileNotFoundError(f"Missing sidecar meta: {meta_path}. Run Phase 2.1 first.")

        # Load normalized document
        with norm_path.open(encoding="utf-8") as f:
            norm_doc = json.load(f)
        normalized_text = norm_doc["normalized_text"]
        content_hash = norm_doc["content_hash"]

        # Load parsed document to get canonical document title
        with parsed_path.open(encoding="utf-8") as f:
            parsed_doc = json.load(f)
        document_title = parsed_doc.get("document_title") or entry.scheme_name

        # Load raw metadata to get last_fetched_at
        with meta_path.open(encoding="utf-8") as f:
            meta_payload = json.load(f)
        last_fetched_at = meta_payload["last_fetched_at"]

        # Generate chunks for this entry
        entry_chunks = chunk_entry(
            entry=entry,
            normalized_text=normalized_text,
            document_title=document_title,
            last_fetched_at=last_fetched_at,
            content_hash=content_hash,
        )
        all_chunks.extend(entry_chunks)

    return all_chunks


def validate_phase2_4(chunks: list[dict[str, Any]] | None = None) -> tuple[bool, list[str]]:
    """Validate that chunks conform strictly to metadata schema and RAG criteria."""
    errors: list[str] = []
    if chunks is None:
        try:
            chunks = chunk_all()
        except Exception as e:
            return False, [f"Failed to generate chunks for validation: {e}"]

    required_fields = {
        "source_url",
        "source_type",
        "amc",
        "scheme_name",
        "scheme_slug",
        "scheme_category",
        "document_title",
        "last_fetched_at",
        "content_hash",
        "chunk_index",
        "text",
    }

    entries = load_inventory()
    allowed_urls = {e.url for e in entries}

    if not chunks:
        errors.append("No chunks were generated")
        return False, errors

    for idx, c in enumerate(chunks):
        # 1. Field validation
        missing = required_fields - set(c.keys())
        if missing:
            errors.append(f"Chunk {idx} missing fields: {missing}")
            continue

        # 2. Closed-list validation
        if c["source_url"] not in allowed_urls:
            errors.append(f"Chunk {idx} references off-list URL: {c['source_url']}")

        # 3. Value validation
        if not c["text"] or not c["text"].strip():
            errors.append(f"Chunk {idx} has empty text")
        if not c["last_fetched_at"]:
            errors.append(f"Chunk {idx} missing last_fetched_at")
        if not c["content_hash"]:
            errors.append(f"Chunk {idx} missing content_hash")

        # 4. Listing vs scheme page validation
        if c["source_type"] == "amc_listing":
            if c["scheme_name"] is not None:
                errors.append(f"Chunk {idx}: amc_listing chunk must have scheme_name: null")
            if c["scheme_category"] is not None:
                errors.append(f"Chunk {idx}: amc_listing chunk must have scheme_category: null")
        else:
            if not c["scheme_name"]:
                errors.append(f"Chunk {idx}: scheme_page chunk must have scheme_name")
            if not c["scheme_category"]:
                errors.append(f"Chunk {idx}: scheme_page chunk must have scheme_category")

    # 5. Check coverage
    urls_with_chunks = {c["source_url"] for c in chunks}
    missing_urls = allowed_urls - urls_with_chunks
    if missing_urls:
        errors.append(f"Missing chunks for URLs: {missing_urls}")

    return len(errors) == 0, errors
