"""Phase 2 ingestion pipeline (subphase packages)."""

from .phase_2_1_fetch import (
    FetchResult,
    fetch_all,
    fetch_entry,
    raw_html_path,
    validate_phase2_1,
)
from .shared.paths import CHUNKS_DIR, NORMALIZED_DIR, PARSED_DIR, RAW_DIR

__all__ = [
    "CHUNKS_DIR",
    "FetchResult",
    "NORMALIZED_DIR",
    "PARSED_DIR",
    "RAW_DIR",
    "fetch_all",
    "fetch_entry",
    "raw_html_path",
    "validate_phase2_1",
]
