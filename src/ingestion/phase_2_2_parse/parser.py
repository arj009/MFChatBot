"""Phase 2.2 — Parse cached Groww HTML into structured JSON."""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from html import unescape
from pathlib import Path
from typing import Any

from bs4 import BeautifulSoup

from src.corpus.inventory import (
    AMC_NAME,
    CorpusEntry,
    EXPECTED_URL_COUNT,
    load_inventory,
    validate_inventory,
)
from src.ingestion.phase_2_1_fetch import raw_html_path
from src.ingestion.shared.next_data import page_props
from src.ingestion.shared.paths import PARSE_MANIFEST_PATH, PARSED_DIR, PROJECT_ROOT

__all__ = [
    "ParsedDocument",
    "parse_all",
    "parse_entry",
    "parsed_json_path",
    "validate_phase2_2",
]

# HTML fallback sections to skip (noisy for facts-only RAG)
_SKIP_SECTION_HEADINGS = frozenset(
    s.lower()
    for s in (
        "Return calculator",
        "Compare similar funds",
        "Fund management",
        "Understand terms",
        "Tax implication",
        "Stamp duty",
        "Expense ratio: in this fund",  # chart section
    )
)


def _should_skip_section(heading: str) -> bool:
    h = heading.lower().strip()
    if any(h.startswith(skip.lower()) for skip in _SKIP_SECTION_HEADINGS):
        return True
    return False


SCHEME_FACT_FIELDS = (
    ("fund_name", "Fund name"),
    ("fund_house", "Fund house"),
    ("category", "Category"),
    ("sub_category", "Sub category"),
    ("expense_ratio", "Expense ratio"),
    ("exit_load", "Exit load"),
    ("min_sip_investment", "Minimum SIP investment"),
    ("min_investment_amount", "Minimum lumpsum investment"),
    ("risk", "Risk"),
    ("nfo_risk", "Riskometer"),
    ("benchmark_name", "Benchmark"),
    ("benchmark", "Benchmark index"),
    ("nav", "NAV"),
    ("nav_date", "NAV date"),
    ("fund_manager", "Fund manager"),
    ("description", "Investment objective"),
    ("meta_desc", "Summary"),
    ("aum", "AUM"),
    ("fund_size", "Fund size"),
)


@dataclass
class ParseResult:
    entry_id: int
    parse_status: str  # ok | failed | skipped
    parsed_path: str | None
    sections_count: int
    text_length: int
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.parse_status == "ok"


@dataclass
class ParsedDocument:
    id: int
    scheme_name: str
    scheme_slug: str | None
    source_type: str
    source_url: str
    document_title: str
    parsed_at: str
    sections: list[dict[str, str]]
    key_facts: dict[str, Any]
    funds_listed: list[dict[str, Any]]
    full_text: str
    raw_text_length: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _repo_relative(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def parsed_json_path(entry: CorpusEntry, parsed_dir: Path | None = None) -> Path:
    return (parsed_dir or PARSED_DIR) / f"{entry.id}.json"


def _extract_title(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    if soup.title and soup.title.string:
        return unescape(soup.title.string.strip())
    og = soup.find("meta", property="og:title")
    if og and og.get("content"):
        return unescape(og["content"].strip())
    return ""


def _html_sections_fallback(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    sections: list[dict[str, str]] = []
    for heading in soup.find_all(["h2", "h3", "h4"]):
        title = heading.get_text(" ", strip=True)
        if not title or len(title) > 120 or _should_skip_section(title):
            continue
        chunks: list[str] = []
        for sibling in heading.find_next_siblings():
            if sibling.name in ("h2", "h3", "h4"):
                break
            text = sibling.get_text(" ", strip=True)
            if text:
                chunks.append(text)
        body = " ".join(chunks).strip()
        if body:
            sections.append({"heading": title, "text": body})
    return sections


def _format_fact_line(label: str, value: Any) -> str:
    if value is None or value == "":
        return ""
    return f"{label}: {value}"


def _format_holdings_section(holdings: list[dict[str, Any]]) -> str:
    """Format holdings data from mfServerSideData into a readable text section."""
    if not holdings or not isinstance(holdings, list):
        return ""
    
    lines = []
    # Get portfolio date from first holding if available
    portfolio_date = None
    if holdings and holdings[0].get("portfolio_date"):
        portfolio_date = holdings[0].get("portfolio_date")
        if portfolio_date:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(portfolio_date.replace("Z", "+00:00"))
                portfolio_date = dt.strftime("%d-%b-%Y")
            except Exception:
                portfolio_date = str(portfolio_date)[:10]
            lines.append(f"Portfolio as of: {portfolio_date}")
            lines.append("")
    
    # Format top holdings (limit to top 20 for brevity)
    top_holdings = holdings[:20]
    lines.append("Top holdings:")
    for i, holding in enumerate(top_holdings, 1):
        company = holding.get("company_name", "N/A")
        sector = holding.get("sector_name", "N/A")
        corpus_per = holding.get("corpus_per")
        market_value = holding.get("market_value")
        
        line = f"{i}. {company}"
        if sector:
            line += f" ({sector})"
        if corpus_per is not None:
            line += f" - {corpus_per:.2f}% of portfolio"
        if market_value is not None:
            line += f" - ₹{market_value:.2f} Cr"
        lines.append(line)
    
    return "\n".join(lines)


def _build_scheme_document(
    entry: CorpusEntry,
    html: str,
    mf: dict[str, Any],
    title: str,
) -> ParsedDocument:
    key_facts: dict[str, Any] = {}
    for field_key, label in SCHEME_FACT_FIELDS:
        if field_key in mf and mf[field_key] not in (None, ""):
            key_facts[field_key] = mf[field_key]

    sections: list[dict[str, str]] = []

    facts_lines = [
        _format_fact_line(label, key_facts.get(key))
        for key, label in SCHEME_FACT_FIELDS
        if key_facts.get(key) not in (None, "")
    ]
    facts_lines = [line for line in facts_lines if line]
    if facts_lines:
        sections.append({"heading": "Key facts", "text": "\n".join(facts_lines)})

    objective = mf.get("description")
    if objective:
        sections.append({"heading": "Investment objective", "text": str(objective).strip()})

    # Extract and format holdings data from mfServerSideData
    holdings = mf.get("holdings")
    if holdings and isinstance(holdings, list) and len(holdings) > 0:
        holdings_text = _format_holdings_section(holdings)
        if holdings_text:
            sections.append({"heading": "Portfolio holdings", "text": holdings_text})

    for section in _html_sections_fallback(html):
        if section["heading"].lower() in {"investment objective", "key facts"}:
            continue
        if not any(s["heading"] == section["heading"] for s in sections):
            sections.append(section)

    full_parts = [f"# {title or entry.scheme_name}"]
    for section in sections:
        full_parts.append(f"\n## {section['heading']}\n{section['text']}")
    full_text = "\n".join(full_parts).strip()

    return ParsedDocument(
        id=entry.id,
        scheme_name=entry.scheme_name,
        scheme_slug=entry.scheme_slug,
        source_type=entry.source_type,
        source_url=entry.url,
        document_title=title or entry.scheme_name,
        parsed_at=_now_iso(),
        sections=sections,
        key_facts=key_facts,
        funds_listed=[],
        full_text=full_text,
        raw_text_length=len(html),
    )


def _build_listing_document(
    entry: CorpusEntry,
    html: str,
    props: dict[str, Any],
    title: str,
) -> ParsedDocument:
    search = props.get("initialSearchResults") or {}
    content = search.get("content") or []
    total = search.get("totalResults", len(content))

    funds_listed: list[dict[str, Any]] = []
    lines: list[str] = [
        f"AMC listing: {AMC_NAME}",
        f"Total schemes listed: {total}",
        "",
    ]

    for fund in content:
        if not isinstance(fund, dict):
            continue
        if fund.get("fund_house") and AMC_NAME.lower() not in str(fund.get("fund_house", "")).lower():
            continue
        row = {
            "fund_name": fund.get("fund_name") or fund.get("scheme_name"),
            "search_id": fund.get("search_id") or fund.get("direct_search_id"),
            "category": fund.get("category"),
            "sub_category": fund.get("sub_category"),
            "expense_ratio": fund.get("expense_ratio"),
            "exit_load": fund.get("exit_load"),
            "min_sip_investment": fund.get("min_sip_investment"),
            "risk": fund.get("risk"),
        }
        funds_listed.append(row)
        lines.append(
            f"- {row['fund_name']}: expense ratio {row.get('expense_ratio')}, "
            f"min SIP {row.get('min_sip_investment')}, risk {row.get('risk')}, "
            f"exit load {row.get('exit_load')}"
        )

    sections = [{"heading": "ICICI Prudential funds (Groww listing)", "text": "\n".join(lines)}]
    full_text = f"# {title or entry.scheme_name}\n\n" + sections[0]["text"]

    return ParsedDocument(
        id=entry.id,
        scheme_name=entry.scheme_name,
        scheme_slug=entry.scheme_slug,
        source_type=entry.source_type,
        source_url=entry.url,
        document_title=title or entry.scheme_name,
        parsed_at=_now_iso(),
        sections=sections,
        key_facts={"total_results": total, "page_batch_size": len(content)},
        funds_listed=funds_listed,
        full_text=full_text,
        raw_text_length=len(html),
    )


def parse_entry(
    entry: CorpusEntry,
    *,
    raw_dir: Path | None = None,
    parsed_dir: Path | None = None,
    force: bool = False,
) -> tuple[ParsedDocument | None, ParseResult]:
    html_path = raw_html_path(entry, raw_dir)
    out_path = parsed_json_path(entry, parsed_dir)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    if not html_path.is_file():
        return None, ParseResult(
            entry_id=entry.id,
            parse_status="failed",
            parsed_path=None,
            sections_count=0,
            text_length=0,
            errors=[f"Missing raw HTML: {html_path}"],
        )

    if not force and out_path.is_file():
        existing = json.loads(out_path.read_text(encoding="utf-8"))
        return None, ParseResult(
            entry_id=entry.id,
            parse_status="skipped",
            parsed_path=_repo_relative(out_path),
            sections_count=len(existing.get("sections", [])),
            text_length=len(existing.get("full_text", "")),
        )

    html = html_path.read_text(encoding="utf-8")
    title = _extract_title(html)
    props = page_props(html)

    try:
        if entry.source_type == "amc_listing":
            if not props:
                raise ValueError("No __NEXT_DATA__ pageProps for listing page")
            doc = _build_listing_document(entry, html, props, title)
        else:
            mf = (props or {}).get("mfServerSideData")
            if not isinstance(mf, dict):
                raise ValueError("No mfServerSideData in __NEXT_DATA__")
            doc = _build_scheme_document(entry, html, mf, title)

        if not doc.full_text.strip():
            raise ValueError("Parsed full_text is empty")

        with out_path.open("w", encoding="utf-8") as f:
            json.dump(doc.to_dict(), f, indent=2, ensure_ascii=False)
            f.write("\n")

        return doc, ParseResult(
            entry_id=entry.id,
            parse_status="ok",
            parsed_path=_repo_relative(out_path),
            sections_count=len(doc.sections),
            text_length=len(doc.full_text),
        )
    except Exception as exc:  # noqa: BLE001 — collect per-URL parse errors
        return None, ParseResult(
            entry_id=entry.id,
            parse_status="failed",
            parsed_path=None,
            sections_count=0,
            text_length=0,
            errors=[str(exc)],
        )


def parse_all(*, force: bool = False) -> tuple[list[ParseResult], Path]:
    entries = load_inventory()
    errors = validate_inventory(entries)
    if errors:
        raise ValueError("Inventory invalid:\n" + "\n".join(errors))

    PARSED_DIR.mkdir(parents=True, exist_ok=True)
    results: list[ParseResult] = []

    for entry in sorted(entries, key=lambda e: e.id):
        _, result = parse_entry(entry, force=force)
        results.append(result)

    manifest = {
        "phase": "2.2",
        "parsed_at": _now_iso(),
        "url_count": len(results),
        "ok_count": sum(1 for r in results if r.parse_status == "ok"),
        "skipped_count": sum(1 for r in results if r.parse_status == "skipped"),
        "failed_count": sum(1 for r in results if r.parse_status == "failed"),
        "results": [asdict(r) for r in results],
    }
    with PARSE_MANIFEST_PATH.open("w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
        f.write("\n")

    return results, PARSE_MANIFEST_PATH


def validate_phase2_2(parsed_dir: Path | None = None) -> tuple[bool, list[str]]:
    directory = parsed_dir or PARSED_DIR
    errors: list[str] = []
    entries = load_inventory()

    if len(entries) != EXPECTED_URL_COUNT:
        errors.append(f"Expected {EXPECTED_URL_COUNT} inventory rows")

    for entry in entries:
        path = parsed_json_path(entry, directory)
        if not path.is_file():
            errors.append(f"Missing parsed JSON for id {entry.id}")
            continue
        data = json.loads(path.read_text(encoding="utf-8"))
        if not (data.get("full_text") or "").strip():
            errors.append(f"Id {entry.id}: empty full_text")
        if entry.source_type == "scheme_page" and not data.get("key_facts"):
            errors.append(f"Id {entry.id}: missing key_facts")
        if entry.source_type == "amc_listing":
            if not data.get("funds_listed"):
                errors.append(f"Id {entry.id}: listing missing funds_listed")

    manifest = PARSE_MANIFEST_PATH
    if not manifest.is_file():
        errors.append("Missing data/parsed/parse_manifest.json")
    elif json.loads(manifest.read_text(encoding="utf-8")).get("failed_count", 0) > 0:
        errors.append("Parse manifest reports failures")

    return len(errors) == 0, errors
