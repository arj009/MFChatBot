"""Phase 1 — Corpus curation: reachability and content validation."""

from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from .inventory import (
    AMC_NAME,
    CORPUS_DIR,
    CorpusEntry,
    EXPECTED_URL_COUNT,
    allowed_url_set,
    is_allowed_url,
    load_inventory,
    normalize_url,
    save_inventory,
    sync_sources_json,
    validate_inventory,
)

CURATION_REPORT_PATH = CORPUS_DIR / "curation_report.json"

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}

CAPTCHA_MARKERS = (
    "captcha",
    "access denied",
    "unusual traffic",
    "please verify",
    "are you a robot",
)

FACT_SIGNALS: dict[str, list[str]] = {
    "expense_ratio": [r"expense\s*ratio", r"ter\b", r"total expense"],
    "exit_load": [r"exit\s*load"],
    "min_sip": [r"min(?:imum)?\s*sip", r"minimum\s*investment", r"min\.?\s*lumpsum"],
    "riskometer": [r"riskometer", r"risk\s*level", r"very high risk"],
}

AMC_FILTER_MARKERS = (
    "icici prudential",
    "icici-prudential",
)


@dataclass
class UrlCurationResult:
    entry_id: int
    url: str
    requested_url_normalized: str
    final_url: str | None
    final_url_normalized: str | None
    http_status: int | None
    reachable: bool
    redirect_ok: bool
    closed_list_ok: bool
    blocked_content: bool
    scheme_title: str | None
    scheme_name_match: bool | None
    amc_filter_ok: bool | None
    fact_signals_found: dict[str, bool] = field(default_factory=dict)
    content_gaps: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    reviewed_at: str = ""

    @property
    def passed(self) -> bool:
        if not self.reachable or not self.redirect_ok or not self.closed_list_ok:
            return False
        if self.blocked_content:
            return False
        if self.amc_filter_ok is False:
            return False
        return True


@dataclass
class CurationReport:
    phase: str = "1"
    amc: str = AMC_NAME
    reviewed_on: str = ""
    url_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    results: list[UrlCurationResult] = field(default_factory=list)
    summary_errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "phase": self.phase,
            "amc": self.amc,
            "reviewed_on": self.reviewed_on,
            "url_count": self.url_count,
            "passed_count": self.passed_count,
            "failed_count": self.failed_count,
            "summary_errors": self.summary_errors,
            "results": [asdict(r) for r in self.results],
        }


def _today_iso() -> str:
    return date.today().isoformat()


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def extract_page_title(html: str) -> str | None:
    og = re.search(
        r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
        html,
        re.I,
    )
    if og:
        return og.group(1).strip()
    title = re.search(r"<title[^>]*>([^<]+)</title>", html, re.I)
    if title:
        return re.sub(r"\s+", " ", title.group(1)).strip()
    return None


def _normalize_name(text: str) -> str:
    lowered = text.lower()
    lowered = re.sub(r"[^\w\s]", " ", lowered)
    return re.sub(r"\s+", " ", lowered).strip()


def scheme_names_align(inventory_name: str, page_title: str | None) -> bool | None:
    if not page_title:
        return None
    inv_tokens = set(_normalize_name(inventory_name).split())
    page_tokens = set(_normalize_name(page_title).split())
    if not inv_tokens or not page_tokens:
        return None
    overlap = inv_tokens & page_tokens
    # Require core fund-house tokens and at least one distinctive token
    required = {"icici", "prudential"}
    if not required.issubset(page_tokens) and not required.issubset(inv_tokens):
        return False
    distinctive = inv_tokens - required - {"fund", "direct", "growth", "plan", "etf", "fof"}
    if distinctive and not (distinctive & page_tokens):
        return False
    return len(overlap) >= 3


def detect_blocked_content(html: str) -> bool:
    sample = html[:8000].lower()
    return any(marker in sample for marker in CAPTCHA_MARKERS)


def scan_fact_signals(html: str, source_type: str) -> tuple[dict[str, bool], list[str]]:
    if source_type == "amc_listing":
        return {}, []

    text = html.lower()
    found = {key: any(re.search(pat, text) for pat in patterns) for key, patterns in FACT_SIGNALS.items()}
    gaps = [key for key, ok in found.items() if not ok]
    return found, gaps


def validate_amc_listing(html: str) -> bool:
    text = html.lower()
    return any(marker in text for marker in AMC_FILTER_MARKERS)


def fetch_url(
    url: str,
    session: requests.Session,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> tuple[int | None, str | None, str | None, list[str]]:
    """Returns (status, final_url, body, errors)."""
    errors: list[str] = []
    last_status: int | None = None

    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            last_status = response.status_code
            if response.status_code == 429:
                wait = 2 ** attempt
                errors.append(f"HTTP 429, retry after {wait}s")
                time.sleep(wait)
                continue
            if response.status_code in (401, 403) and attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
                errors.append(f"HTTP {response.status_code}, retrying")
                continue
            body = response.text if response.ok else response.text[:5000]
            return response.status_code, response.url, body, errors
        except requests.RequestException as exc:
            errors.append(str(exc))
            if attempt < max_retries - 1:
                time.sleep(1.5 * (attempt + 1))
            else:
                return last_status, None, None, errors

    return last_status, None, None, errors


def curate_entry(
    entry: CorpusEntry,
    session: requests.Session,
    allowed: frozenset[str],
) -> UrlCurationResult:
    reviewed_at = _now_iso()
    requested_norm = normalize_url(entry.url)
    result = UrlCurationResult(
        entry_id=entry.id,
        url=entry.url,
        requested_url_normalized=requested_norm,
        final_url=None,
        final_url_normalized=None,
        http_status=None,
        reachable=False,
        redirect_ok=False,
        closed_list_ok=False,
        blocked_content=False,
        scheme_title=None,
        scheme_name_match=None,
        amc_filter_ok=None,
        reviewed_at=reviewed_at,
    )

    status, final_url, body, fetch_errors = fetch_url(entry.url, session)
    result.http_status = status
    result.errors.extend(fetch_errors)

    if status is None or final_url is None:
        result.errors.append("Request failed")
        return result

    result.final_url = final_url
    result.final_url_normalized = normalize_url(final_url)
    result.reachable = status == 200 and bool(body)
    result.closed_list_ok = is_allowed_url(final_url) and result.final_url_normalized in allowed

    result.redirect_ok = result.final_url_normalized == requested_norm
    if not result.redirect_ok:
        result.errors.append(
            f"Redirect mismatch after normalize: {result.final_url_normalized} != {requested_norm}"
        )

    if not result.reachable:
        result.errors.append(f"HTTP {status} or empty body")
        return result

    assert body is not None
    if detect_blocked_content(body):
        result.blocked_content = True
        result.errors.append("Blocked or CAPTCHA-like content detected")
        return result

    if entry.source_type == "amc_listing":
        result.amc_filter_ok = validate_amc_listing(body)
        if not result.amc_filter_ok:
            result.errors.append("AMC filter page missing ICICI Prudential markers")
        return result

    result.scheme_title = extract_page_title(body)
    result.scheme_name_match = scheme_names_align(entry.scheme_name, result.scheme_title)
    if result.scheme_name_match is False:
        result.errors.append(
            f"Title mismatch (review metadata): inventory='{entry.scheme_name}' "
            f"title='{result.scheme_title}'"
        )

    result.fact_signals_found, gaps = scan_fact_signals(body, entry.source_type)
    result.content_gaps = gaps
    if gaps:
        result.errors.append(f"Content gaps (non-fatal): {', '.join(gaps)}")

    return result


def validate_phase1_metadata(entries: list[CorpusEntry]) -> list[str]:
    errors = validate_inventory(entries)
    for e in entries:
        if not e.last_reviewed:
            errors.append(f"Row {e.id}: last_reviewed is required after Phase 1")
    return errors


def run_curation(
    *,
    request_delay: float = 1.0,
    update_inventory: bool = True,
    entries: list[CorpusEntry] | None = None,
) -> CurationReport:
    items = entries if entries is not None else load_inventory()
    structural = validate_inventory(items)
    if structural:
        raise ValueError("Inventory invalid:\n" + "\n".join(f"  - {e}" for e in structural))

    allowed = allowed_url_set(items)
    report = CurationReport(
        reviewed_on=_today_iso(),
        url_count=len(items),
    )

    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    updated_rows: list[dict[str, str]] = []

    for entry in sorted(items, key=lambda e: e.id):
        if request_delay > 0 and entry.id > 1:
            time.sleep(request_delay)

        result = curate_entry(entry, session, allowed)
        report.results.append(result)

        if result.passed:
            report.passed_count += 1
        else:
            report.failed_count += 1

        row = {
            "id": str(entry.id),
            "scheme_name": entry.scheme_name,
            "category": entry.category,
            "url": entry.url,
            "scheme_slug": entry.scheme_slug or "",
            "source_type": entry.source_type,
            "status": "approved" if result.passed else "failed",
            "last_reviewed": _today_iso() if result.passed else "",
        }
        updated_rows.append(row)

    if report.failed_count:
        report.summary_errors.append(
            f"{report.failed_count} of {report.url_count} URLs failed reachability checks"
        )

    report_path = CURATION_REPORT_PATH
    with report_path.open("w", encoding="utf-8") as f:
        json.dump(report.to_dict(), f, indent=2, ensure_ascii=False)
        f.write("\n")

    if update_inventory and report.failed_count == 0:
        save_inventory(updated_rows)
        sync_sources_json()
    elif update_inventory and report.failed_count > 0:
        # Still record review date for passed rows only
        partial = []
        for entry, result, row in zip(
            sorted(items, key=lambda e: e.id), report.results, updated_rows
        ):
            partial.append(
                {
                    **row,
                    "status": "approved" if result.passed else entry.status,
                    "last_reviewed": _today_iso() if result.passed else entry.last_reviewed,
                }
            )
        save_inventory(partial)

    return report


def load_curation_report(path: Path | None = None) -> dict[str, Any] | None:
    report_path = path or CURATION_REPORT_PATH
    if not report_path.is_file():
        return None
    with report_path.open(encoding="utf-8") as f:
        return json.load(f)


def phase1_exit_ok(report: CurationReport | None = None) -> tuple[bool, list[str]]:
    errors: list[str] = []
    entries = load_inventory()

    errors.extend(validate_phase1_metadata(entries) if all(e.last_reviewed for e in entries) else [])
    if len(entries) != EXPECTED_URL_COUNT:
        errors.append(f"Expected {EXPECTED_URL_COUNT} URLs")

    pending = [e for e in entries if e.status != "approved"]
    if pending:
        errors.append(f"{len(pending)} URLs not approved")

    if report is None:
        report_data = load_curation_report()
        if not report_data:
            errors.append("Missing corpus/curation_report.json — run scripts/curate_corpus.py")
            return False, errors
        if report_data.get("failed_count", 1) != 0:
            errors.append("Curation report has failures")
    else:
        if report.failed_count != 0:
            errors.append(f"Curation failures: {report.failed_count}")

    if not errors and not all(e.last_reviewed for e in entries):
        errors.append("All rows must have last_reviewed set")

    return len(errors) == 0, errors
