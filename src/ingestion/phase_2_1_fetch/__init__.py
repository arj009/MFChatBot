"""Phase 2.1 — Closed-list fetch and raw HTML cache."""

from .fetcher import (
    FetchResult,
    fetch_all,
    fetch_entry,
    raw_basename,
    raw_html_path,
    raw_meta_path,
    validate_phase2_1,
)

__all__ = [
    "FetchResult",
    "fetch_all",
    "fetch_entry",
    "raw_basename",
    "raw_html_path",
    "raw_meta_path",
    "validate_phase2_1",
]
