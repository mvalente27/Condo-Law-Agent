"""Lightweight anonymization for sensitive association documents.

Strips obvious unit owner names, street addresses, unit numbers, emails, and
phone numbers before text is sent to the external API. This is a heuristic
layer; firms should layer additional redaction for litigation-grade use.
"""
from __future__ import annotations

import re

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b")
ADDRESS_RE = re.compile(
    r"\b\d{1,6}\s+[A-Z][A-Za-z0-9.\-']*(?:\s+[A-Z][A-Za-z0-9.\-']*){0,4}\s+"
    r"(?:Street|St\.?|Avenue|Ave\.?|Road|Rd\.?|Boulevard|Blvd\.?|Drive|Dr\.?|"
    r"Lane|Ln\.?|Court|Ct\.?|Way|Place|Pl\.?|Terrace|Ter\.?|Circle|Cir\.?|"
    r"Highway|Hwy\.?|Parkway|Pkwy\.?)\b",
)
UNIT_RE = re.compile(r"\bUnit\s+(?:No\.?\s*)?[A-Z0-9\-]+\b", re.IGNORECASE)
ZIP_RE = re.compile(r"\b\d{5}(?:-\d{4})?\b")
# Conservative person-name heuristic: two consecutive Capitalized words,
# excluding common legal/document terms.
NAME_RE = re.compile(r"\b([A-Z][a-z]{1,20})\s+([A-Z][a-z]{1,20})\b")
NAME_STOPWORDS = {
    "Master", "Deed", "Bylaws", "Board", "Trust", "Trustees", "Unit", "Owner",
    "Common", "Area", "Areas", "Section", "Article", "Schedule", "Exhibit",
    "Massachusetts", "Connecticut", "Rhode", "Island", "Vermont", "Maine",
    "Hampshire", "United", "States", "Land", "Court", "Supreme", "Judicial",
    "Appeals", "Superior", "District", "County", "Condominium", "Association",
    "Declaration", "Amendment", "Rules", "Regulations",
}


def anonymize(text: str) -> str:
    if not text:
        return text
    text = EMAIL_RE.sub("[REDACTED_EMAIL]", text)
    text = PHONE_RE.sub("[REDACTED_PHONE]", text)
    text = ADDRESS_RE.sub("[REDACTED_ADDRESS]", text)
    text = UNIT_RE.sub("[REDACTED_UNIT]", text)
    text = ZIP_RE.sub("[REDACTED_ZIP]", text)

    def _name_sub(m: re.Match[str]) -> str:
        a, b = m.group(1), m.group(2)
        if a in NAME_STOPWORDS or b in NAME_STOPWORDS:
            return m.group(0)
        return "[REDACTED_NAME]"

    text = NAME_RE.sub(_name_sub, text)
    return text
