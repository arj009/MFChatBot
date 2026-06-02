"""Phase 2.3 — Normalize parsed documents and compute content hashes."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from src.corpus.inventory import (
    CorpusEntry,
    EXPECTED_URL_COUNT,
    load_inventory,
    validate_inventory,
)

from src.ingestion.phase_2_2_parse.parser import parsed_json_path
from src.ingestion.shared.paths import NORMALIZED_DIR, NORMALIZE_MANIFEST_PATH, PROJECT_ROOT

__all__ = [
    "NormalizedDocument",
    "normalize_all",
    "normalize_entry",
    "normalized_json_path",
    "validate_phase2_3",
    "compute_content_hash",
]

FACT_SIGNAL_PATTERNS: dict[str, list[str]] = {
    "expense_ratio": [r"expense\s*ratio"],
    "exit_load": [r"exit\s*load"],
    "min_sip": [r"min(?:imum)?\s*sip", r"minimum\s*sip"],
    "riskometer": [r"riskometer", r"\brisk\b", r"very high risk"],
}

BOILERPLATE_PATTERNS = [
    r"groww\.in",
    r"accept\s*cookies?",
    r"download\s*app",
    r"sign\s*up\s*now",
    r"©\s*\d{4}",
]

SPOT_CHECK_IDS = {
    "expense_ratio": 3,   # Large Cap
    "exit_load": 19,      # Liquid
    "min_sip": 22,        # Flexicap
}


@dataclass
class NormalizeResult:
    entry_id: int
    normalize_status: str  # ok | failed | skipped
    normalized_path: str | None
    content_hash: str | None
    char_count: int
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.normalize_status == "ok"


@dataclass
class NormalizedDocument:
    id: int
    source_url: str
    source_type: str
    scheme_name: str
    normalized_at: str
    normalized_text: str
    content_hash: str
    char_count: int
    fact_signals: dict[str, bool]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def normalized_json_path(entry: CorpusEntry, normalized_dir: Path | None = None) -> Path:
    return (normalized_dir or NORMALIZED_DIR) / f"{entry.id}.json"


def compute_content_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _collapse_whitespace(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _strip_boilerplate(text: str) -> str:
    lines: list[str] = []
    for line in text.split("\n"):
        lower = line.lower()
        if any(re.search(pat, lower) for pat in BOILERPLATE_PATTERNS):
            continue
        lines.append(line.strip())
    return _collapse_whitespace("\n".join(lines))


def _scan_fact_signals(text: str) -> dict[str, bool]:
    lower = text.lower()
    return {
        key: any(re.search(pat, lower) for pat in patterns)
        for key, patterns in FACT_SIGNAL_PATTERNS.items()
    }


def normalize_text(parsed: dict[str, Any]) -> str:
    """Build normalized plain text from parsed document."""
    text = (parsed.get("full_text") or "").strip()
    if not text and parsed.get("sections"):
        parts = []
        for section in parsed["sections"]:
            heading = section.get("heading", "").strip()
            body = section.get("text", "").strip()
            if heading:
                parts.append(f"## {heading}")
            if body:
                parts.append(body)
        text = "\n\n".join(parts)
    return _strip_boilerplate(text)


def normalize_entry(
    entry: CorpusEntry,
    *,
    parsed_dir: Path | None = None,
    normalized_dir: Path | None = None,
    force: bool = False,
) -> tuple[NormalizedDocument | None, NormalizeResult]:
    parsed_path = parsed_json_path(entry, parsed_dir)
    out_path = normalized_json_path(entry, normalized_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not parsed_path.is_file():
        return None, NormalizeResult(
            entry_id=entry.id,
            normalize_status="failed",
            normalized_path=None,
            content_hash=None,
            char_count=0,
            errors=[f"Missing parsed file: {parsed_path}. Run Phase 2.2 first."],
        )

    if not force and out_path.is_file():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        return None, NormalizeResult(
            entry_id=entry.id,
            normalize_status="skipped",
            normalized_path=_repo_relative(out_path),
            content_hash=existing.get("content_hash"),
            char_count=existing.get("char_count", 0),
        )

    try:
        parsed = json.loads(parsed_path.read_text(encoding="utf-8"))
        normalized_text = normalize_text(parsed)
        if not normalized_text:
            raise ValueError("Normalized text is empty")

        content_hash = compute_content_hash(normalized_text)
        fact_signals = _scan_fact_signals(normalized_text)

        doc = NormalizedDocument(
            id=entry.id,
            source_url=parsed.get("source_url", entry.url),
            source_type=parsed.get("source_type", entry.source_type),
            scheme_name=parsed.get("scheme_name", entry.scheme_name),
            normalized_at=_now_iso(),
            normalized_text=normalized_text,
            content_hash=content_hash,
            char_count=len(normalized_text),
            fact_signals=fact_signals,
        )

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)
            f.write("\n")

        return doc, NormalizeResult(
            entry_id=entry.id,
            normalize_status="ok",
            normalized_path=_repo_relative(out_path),
            content_hash=content_hash,
            char_count=len(normalized_text),
        )
    except Exception as exc:  # noqa: BLE001
        return None, NormalizeResult(
            entry_id=entry.id,
            normalize_status="failed",
            normalized_path=None,
            content_hash=None,
            char_count=0,
            errors=[str(exc)],
        )


def normalize_all(*, force: bool = False) -> tuple[list[NormalizeResult], Path]:
    entries = load_inventory()
    errors = validate_inventory(entries)
    if errors:
        raise ValueError("Inventory invalid:\n" + "\n".join(errors))

    NORMALIZED_DIR.mkdir(parents=True, exist_ok=True)
    results: list[NormalizeResult] = []

    for entry in sorted(entries, key=lambda e: e.id):
        _, result = normalize_entry(entry, force=force)
        results.append(result)

    manifest = {
        "phase": "2.3",
        "normalized_at": _now_iso(),
        "url_count": len(results),
        "ok_count": sum(1 for r in results if r.normalize_status == "ok"),
        "skipped_count": sum(1 for r in results if r.normalize_status == "skipped"),
        "failed_count": sum(1 for r in results if r.normalize_status == "failed"),
        "results": [asdict(r) for r in results],
    }
    with NORMALIZE_MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return results, NORMALIZE_MANIFEST_PATH


def validate_phase2_3(normalized_dir: Path | None = None) -> tuple[bool, list[str]]:
    directory = normalized_dir or NORMALIZED_DIR
    errors: list[str] = []
    entries = load_inventory()

    for entry in entries:
        path = normalized_json_path(entry, directory)
        if not path.is_file():
            errors.append(f"Missing normalized JSON for id {entry.id}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not (data.get("normalized_text") or "").strip():
            errors.append(f"Id {entry.id}: empty normalized_text")
        if not data.get("content_hash"):
            errors.append(f"Id {entry.id}: missing content_hash")

    for signal, entry_id in SPOT_CHECK_IDS.items():
        path = normalized_json_path(
            next(e for e in entries if e.id == entry_id), directory
        )
        if path.is_file():
            text = json.loads(path.read_text(encoding="utf-8")).get("normalized_text", "")
            pattern = FACT_SIGNAL_PATTERNS[signal][0]
            if not re.search(pattern, text, re.I):
                errors.append(f"Spot-check id {entry_id}: '{signal}' not found in normalized text")

    manifest = NORMALIZE_MANIFEST_PATH
    if not manifest.is_file():
        errors.append("Missing data/normalized/normalize_manifest.json")
    elif json.loads(manifest.read_text(encoding="utf-8")).get("failed_count", 0) > 0:
        errors.append("Normalize manifest reports failures")

    if len(entries) != EXPECTED_URL_COUNT:
        errors.append(f"Expected {EXPECTED_URL_COUNT} inventory rows")

    return len(errors) == 0, errors
