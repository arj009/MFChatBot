"""Phase 2.1 — Closed-list fetch and raw HTML cache."""

from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests

from src.corpus.inventory import (
    ClosedCorpusError,
    CorpusEntry,
    EXPECTED_URL_COUNT,
    allowed_url_set,
    enforce_closed_url,
    load_inventory,
    normalize_url,
    validate_inventory,
)
from src.ingestion.shared.http_client import create_session, fetch_html
from src.ingestion.shared.paths import FETCH_MANIFEST_PATH, PROJECT_ROOT, RAW_DIR

__all__ = [
    "FetchResult",
    "RAW_DIR",
    "FETCH_MANIFEST_PATH",
    "fetch_all",
    "fetch_entry",
    "raw_basename",
    "raw_html_path",
    "raw_meta_path",
    "validate_phase2_1",
]


@dataclass
class FetchResult:
    entry_id: int
    requested_url: str
    final_url: str | None
    http_status: int | None
    fetch_status: str  # ok | failed | skipped
    last_fetched_at: str
    html_path: str | None
    meta_path: str | None
    content_bytes: int
    redirect_ok: bool
    closed_list_ok: bool
    off_list_violation: bool = False
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.fetch_status == "ok" and self.html_path is not None


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo_relative_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def raw_basename(entry: CorpusEntry) -> str:
    if entry.scheme_slug:
        return f"{entry.id}_{entry.scheme_slug}"
    return str(entry.id)


def raw_html_path(entry: CorpusEntry, raw_dir: Path | None = None) -> Path:
    return (raw_dir or RAW_DIR) / f"{raw_basename(entry)}.html"


def raw_meta_path(entry: CorpusEntry, raw_dir: Path | None = None) -> Path:
    return (raw_dir or RAW_DIR) / f"{raw_basename(entry)}.meta.json"


def load_sidecar(meta_path: Path) -> dict[str, Any] | None:
    if not meta_path.is_file():
        return None
    with meta_path.open(encoding="utf-8") as f:
        return json.load(f)


def write_sidecar(meta_path: Path, payload: dict[str, Any]) -> None:
    meta_path.parent.mkdir(parents=True, exist_ok=True)
    with meta_path.open("w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
        f.write("\n")


def fetch_entry(
    entry: CorpusEntry,
    session: requests.Session,
    allowed: frozenset[str],
    *,
    raw_dir: Path | None = None,
    force: bool = False,
) -> FetchResult:
    """Fetch one inventory URL; write HTML + sidecar metadata."""
    directory = raw_dir or RAW_DIR
    directory.mkdir(parents=True, exist_ok=True)

    html_path = raw_html_path(entry, directory)
    meta_path = raw_meta_path(entry, directory)
    fetched_at = _now_iso()
    requested_norm = normalize_url(entry.url)

    if entry.status != "approved":
        return FetchResult(
            entry_id=entry.id,
            requested_url=entry.url,
            final_url=None,
            http_status=None,
            fetch_status="failed",
            last_fetched_at=fetched_at,
            html_path=None,
            meta_path=None,
            content_bytes=0,
            redirect_ok=False,
            closed_list_ok=False,
            errors=[f"Inventory status is '{entry.status}', expected 'approved'"],
        )

    if not force and html_path.is_file() and meta_path.is_file():
        sidecar = load_sidecar(meta_path) or {}
        return FetchResult(
            entry_id=entry.id,
            requested_url=entry.url,
            final_url=sidecar.get("final_url"),
            http_status=sidecar.get("http_status"),
            fetch_status="skipped",
            last_fetched_at=sidecar.get("last_fetched_at", fetched_at),
            html_path=_repo_relative_path(html_path),
            meta_path=_repo_relative_path(meta_path),
            content_bytes=html_path.stat().st_size,
            redirect_ok=True,
            closed_list_ok=True,
        )

    try:
        enforce_closed_url(entry.url)
    except ClosedCorpusError as exc:
        return FetchResult(
            entry_id=entry.id,
            requested_url=entry.url,
            final_url=None,
            http_status=None,
            fetch_status="failed",
            last_fetched_at=fetched_at,
            html_path=None,
            meta_path=None,
            content_bytes=0,
            redirect_ok=False,
            closed_list_ok=False,
            off_list_violation=True,
            errors=[str(exc)],
        )

    status, final_url, body, fetch_errors = fetch_html(entry.url, session)
    result = FetchResult(
        entry_id=entry.id,
        requested_url=entry.url,
        final_url=final_url,
        http_status=status,
        fetch_status="failed",
        last_fetched_at=fetched_at,
        html_path=None,
        meta_path=None,
        content_bytes=0,
        redirect_ok=False,
        closed_list_ok=False,
        errors=list(fetch_errors),
    )

    if status is None or final_url is None or body is None:
        result.errors.append("Request failed")
        _write_failed_sidecar(meta_path, entry, result)
        return result

    final_norm = normalize_url(final_url)
    result.final_url = final_url
    result.closed_list_ok = final_norm in allowed
    result.redirect_ok = final_norm == requested_norm

    if not result.closed_list_ok:
        result.off_list_violation = True
        result.errors.append(f"Final URL not in closed corpus: {final_url}")
        _write_failed_sidecar(meta_path, entry, result)
        return result

    if not result.redirect_ok:
        result.errors.append(f"Redirect mismatch: {final_norm} != {requested_norm}")

    if status != 200:
        result.errors.append(f"HTTP {status}")
        _write_failed_sidecar(meta_path, entry, result)
        return result

    html_path.write_text(body, encoding="utf-8")
    result.content_bytes = len(body.encode("utf-8"))
    result.fetch_status = "ok"
    result.html_path = _repo_relative_path(html_path)
    result.meta_path = _repo_relative_path(meta_path)

    write_sidecar(meta_path, _sidecar_payload(entry, result))
    return result


def _sidecar_payload(entry: CorpusEntry, result: FetchResult) -> dict[str, Any]:
    return {
        "id": entry.id,
        "scheme_name": entry.scheme_name,
        "scheme_slug": entry.scheme_slug,
        "source_type": entry.source_type,
        "requested_url": entry.url,
        "final_url": result.final_url,
        "http_status": result.http_status,
        "fetch_status": result.fetch_status,
        "last_fetched_at": result.last_fetched_at,
        "content_bytes": result.content_bytes,
        "redirect_ok": result.redirect_ok,
        "closed_list_ok": result.closed_list_ok,
        "errors": result.errors,
    }


def _write_failed_sidecar(meta_path: Path, entry: CorpusEntry, result: FetchResult) -> None:
    write_sidecar(meta_path, _sidecar_payload(entry, result))


def fetch_all(
    *,
    entries: list[CorpusEntry] | None = None,
    raw_dir: Path | None = None,
    request_delay: float = 1.0,
    force: bool = False,
) -> tuple[list[FetchResult], Path]:
    """Fetch all approved inventory URLs; write manifest."""
    items = entries if entries is not None else load_inventory()
    structural = validate_inventory(items)
    if structural:
        raise ValueError("Inventory invalid:\n" + "\n".join(f"  - {e}" for e in structural))

    allowed = allowed_url_set(items)
    session = create_session()
    directory = raw_dir or RAW_DIR
    directory.mkdir(parents=True, exist_ok=True)

    results: list[FetchResult] = []
    for entry in sorted(items, key=lambda e: e.id):
        if request_delay > 0 and entry.id > 1:
            time.sleep(request_delay)
        results.append(
            fetch_entry(entry, session, allowed, raw_dir=directory, force=force)
        )

    manifest_path = directory / "fetch_manifest.json"
    with manifest_path.open("w", encoding="utf-8") as f:
        json.dump(_build_manifest(results), f, indent=2, ensure_ascii=False)
        f.write("\n")

    return results, manifest_path


def _build_manifest(results: list[FetchResult]) -> dict[str, Any]:
    return {
        "phase": "2.1",
        "fetched_at": _now_iso(),
        "url_count": len(results),
        "ok_count": sum(1 for r in results if r.fetch_status == "ok"),
        "skipped_count": sum(1 for r in results if r.fetch_status == "skipped"),
        "failed_count": sum(1 for r in results if r.fetch_status == "failed"),
        "off_list_violations": sum(1 for r in results if r.off_list_violation),
        "results": [asdict(r) for r in results],
    }


def validate_phase2_1(raw_dir: Path | None = None) -> tuple[bool, list[str]]:
    """Check Phase 2.1 exit criteria."""
    directory = raw_dir or RAW_DIR
    errors: list[str] = []
    entries = load_inventory()

    if len(entries) != EXPECTED_URL_COUNT:
        errors.append(f"Expected {EXPECTED_URL_COUNT} inventory rows")

    missing_html: list[int] = []
    missing_meta: list[int] = []
    for entry in entries:
        html = raw_html_path(entry, directory)
        meta = raw_meta_path(entry, directory)
        if not html.is_file():
            missing_html.append(entry.id)
        if not meta.is_file():
            missing_meta.append(entry.id)
        else:
            sidecar = load_sidecar(meta) or {}
            if not sidecar.get("last_fetched_at"):
                errors.append(f"Row {entry.id}: sidecar missing last_fetched_at")

    if missing_html:
        errors.append(f"Missing HTML for ids: {missing_html}")
    if missing_meta:
        errors.append(f"Missing sidecar for ids: {missing_meta}")

    manifest_path = directory / "fetch_manifest.json"
    if not manifest_path.is_file():
        errors.append("Missing data/raw/fetch_manifest.json")
    else:
        with manifest_path.open(encoding="utf-8") as f:
            manifest = json.load(f)
        if manifest.get("off_list_violations", 0) != 0:
            errors.append("Manifest reports off-list URL violations")
        if manifest.get("failed_count", 0) > 0:
            errors.append(f"Manifest failed_count={manifest['failed_count']}")

    return len(errors) == 0, errors
