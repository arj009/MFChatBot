"""Extract embedded Next.js payload from Groww HTML."""

from __future__ import annotations

import json
import re
from typing import Any

_NEXT_DATA_PATTERN = re.compile(
    r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>',
    re.DOTALL,
)


def extract_next_data(html: str) -> dict[str, Any] | None:
    match = _NEXT_DATA_PATTERN.search(html)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def page_props(html: str) -> dict[str, Any] | None:
    data = extract_next_data(html)
    if not data:
        return None
    props = data.get("props", {}).get("pageProps")
    return props if isinstance(props, dict) else None
