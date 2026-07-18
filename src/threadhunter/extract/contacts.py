"""Regex-based contact extraction from post text.

Extracts phone numbers, Telegram usernames, and email addresses.
All values are normalised (phones → E.164-like, usernames/emails → lowercase).
"""

from __future__ import annotations

import re
from dataclasses import dataclass

__all__ = ["ExtractedContact", "extract_contacts"]


@dataclass(frozen=True)
class ExtractedContact:
    """A single contact extracted from post text."""

    type: str  # "phone" | "telegram" | "email"
    value: str  # normalised value


# ---------------------------------------------------------------------------
# Phone patterns
# ---------------------------------------------------------------------------
# Matches:
#   +996 XXX XXX XXX  (Kyrgyzstan)
#   +7 XXX XXX XX XX  (Russia / Kazakhstan)
#   8 XXX XXX XX XX   (Russian domestic, requires at least one separator)
#
# Separators between digit groups: space, dash, or dot.
_PHONE_PATTERNS = [
    # +996 with optional separator, then groups of digits
    r"(?<!\d)\+996[\s.\-]?\(?\d{1,4}\)?[\s.\-]?\d{1,4}[\s.\-]?\d{1,4}(?:[\s.\-]?\d{1,4})*",
    # +7 with optional separator, then groups of digits
    r"(?<!\d)\+7[\s.\-]?\(?\d{1,4}\)?[\s.\-]?\d{1,4}[\s.\-]?\d{1,4}(?:[\s.\-]?\d{1,4})*",
    # 8 prefix (Russian domestic) — requires at least one separator to avoid
    # false positives on ordinary numbers like "8 apples"
    r"(?<!\d)8[\s.\-]\d{3}[\s.\-]?\d{3}[\s.\-]?\d{2}[\s.\-]?\d{2}",
]

_PHONE_RE = re.compile("|".join(_PHONE_PATTERNS))

# ---------------------------------------------------------------------------
# Telegram username: @ followed by 3-32 chars (letters, digits, underscore)
# ---------------------------------------------------------------------------
_TELEGRAM_RE = re.compile(r"(?<![a-zA-Z0-9_])@([A-Za-z][A-Za-z0-9_]{2,31})")

# ---------------------------------------------------------------------------
# Email: standard RFC-5322-ish pattern
# ---------------------------------------------------------------------------
_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")


def extract_contacts(text: str) -> list[ExtractedContact]:
    """Extract all contacts from *text*.

    Returns a deduplicated list of ``ExtractedContact`` sorted by
    ``(type, value)``.
    """
    if not text:
        return []

    results: list[ExtractedContact] = []

    # Phones
    for m in _PHONE_RE.finditer(text):
        normalised = _normalize_phone(m.group())
        if normalised is not None:
            results.append(ExtractedContact(type="phone", value=normalised))

    # Telegram usernames
    for m in _TELEGRAM_RE.finditer(text):
        username = m.group(1).lower()
        results.append(ExtractedContact(type="telegram", value=username))

    # Emails
    for m in _EMAIL_RE.finditer(text):
        email = m.group(0).lower()
        results.append(ExtractedContact(type="email", value=email))

    # Deduplicate by (type, value)
    seen: set[tuple[str, str]] = set()
    unique: list[ExtractedContact] = []
    for c in results:
        key = (c.type, c.value)
        if key not in seen:
            seen.add(key)
            unique.append(c)

    return sorted(unique, key=lambda c: (c.type, c.value))


def _normalize_phone(raw: str) -> str | None:
    """Normalise a phone number to ``+XXXXXXXXXXX`` format.

    Returns ``None`` if the number cannot be normalised (too few/many digits,
    unrecognised country code).
    """
    digits = re.sub(r"\D", "", raw)

    # Russian domestic: 8XXXXXXXXXX (11 digits) → +7XXXXXXXXXX
    if len(digits) == 11 and digits[0] == "8":
        digits = "7" + digits[1:]

    # Kazakhstan: 7XXXXX… (11 digits starting with 7) is already correct
    # Kyrgyzstan: 996XXXXXX (12 digits starting with 996) is already correct
    # Russia intl: 7XXXXXXXXXX (11 digits starting with 7) is already correct

    if len(digits) < 10 or len(digits) > 12:
        return None

    return f"+{digits}"
