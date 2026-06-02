"""Shared HTTP client for Phase 1 curation and Phase 2.1 fetch."""

from __future__ import annotations

import time

import requests

DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
}


def create_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)
    return session


def fetch_html(
    url: str,
    session: requests.Session,
    *,
    timeout: float = 30.0,
    max_retries: int = 3,
) -> tuple[int | None, str | None, str | None, list[str]]:
    """Returns (status_code, final_url, html_body, errors)."""
    errors: list[str] = []
    last_status: int | None = None

    for attempt in range(max_retries):
        try:
            response = session.get(url, timeout=timeout, allow_redirects=True)
            last_status = response.status_code
            if response.status_code == 429:
                wait = 2**attempt
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
