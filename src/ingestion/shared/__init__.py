"""Shared utilities for all Phase 2 subphases."""

from .http_client import create_session, fetch_html
from .paths import (
    CHUNKS_DIR,
    NORMALIZED_DIR,
    PARSED_DIR,
    PROJECT_ROOT,
    RAW_DIR,
)

__all__ = [
    "CHUNKS_DIR",
    "NORMALIZED_DIR",
    "PARSED_DIR",
    "PROJECT_ROOT",
    "RAW_DIR",
    "create_session",
    "fetch_html",
]
