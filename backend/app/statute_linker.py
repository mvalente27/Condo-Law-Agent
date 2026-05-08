"""Convert statute citations in model output into hyperlinks."""
from __future__ import annotations

import re

# (state) -> list of (compiled regex, url builder)
_PATTERNS: dict[str, list[tuple[re.Pattern[str], object]]] = {
    "MA": [
        (
            re.compile(r"\bM\.?G\.?L\.?\s*c\.?\s*183A(?:[,\s]+§\s*([0-9A-Za-z\-]+))?", re.IGNORECASE),
            lambda m: (
                "https://malegislature.gov/Laws/GeneralLaws/PartII/TitleI/Chapter183A"
                + (f"/Section{m.group(1)}" if m.group(1) else "")
            ),
        ),
        (
            re.compile(r"\bChapter\s+183A(?:[,\s]+§\s*([0-9A-Za-z\-]+))?", re.IGNORECASE),
            lambda m: (
                "https://malegislature.gov/Laws/GeneralLaws/PartII/TitleI/Chapter183A"
                + (f"/Section{m.group(1)}" if m.group(1) else "")
            ),
        ),
    ],
    "CT": [
        (
            re.compile(r"\bC\.?G\.?S\.?\s*§?\s*47-(\d{1,3}[a-z]?)", re.IGNORECASE),
            lambda m: f"https://www.cga.ct.gov/current/pub/chap_828.htm#sec_47-{m.group(1)}",
        ),
    ],
    "RI": [
        (
            re.compile(r"\bR\.?I\.?\s*Gen\.?\s*Laws?\s*§?\s*34-36\.?1?-(\d+(?:\.\d+)?)", re.IGNORECASE),
            lambda m: f"http://webserver.rilegislature.gov/Statutes/TITLE34/34-36.1/34-36.1-{m.group(1)}.HTM",
        ),
    ],
    "NH": [
        (
            re.compile(r"\bRSA\s*356-B:(\d+)", re.IGNORECASE),
            lambda m: f"https://www.gencourt.state.nh.us/rsa/html/XXXI/356-B/356-B-{m.group(1)}.htm",
        ),
    ],
    "VT": [
        (
            re.compile(r"\b27A\s*V\.?S\.?A\.?\s*§?\s*(\d-\d+)", re.IGNORECASE),
            lambda m: f"https://legislature.vermont.gov/statutes/section/27A/{m.group(1).split('-')[0]}/{m.group(1)}",
        ),
    ],
    "ME": [
        (
            re.compile(r"\b33\s*M\.?R\.?S\.?\s*§?\s*(160[1-9]|16[1-9]\d|1[7-9]\d\d)", re.IGNORECASE),
            lambda m: f"https://legislature.maine.gov/statutes/33/title33sec{m.group(1)}.html",
        ),
    ],
}


def linkify(text: str, state: str | None) -> str:
    if not state:
        return text
    patterns = _PATTERNS.get(state.upper(), [])
    for rx, build in patterns:
        def _sub(m: re.Match[str], _b=build) -> str:
            url = _b(m)
            return f"[{m.group(0)}]({url})"
        text = rx.sub(_sub, text)
    return text
