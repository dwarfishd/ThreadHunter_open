"""Rules-based tag classification for post text.

Rules are loaded from ``data/tags-rules.yaml`` at the project root.
Three tag types are supported: ``location``, ``assortment``, ``offer_type``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

__all__ = ["ExtractedTag", "classify_tags"]


@dataclass(frozen=True)
class ExtractedTag:
    """A single tag classified from post text."""

    type: str  # "location" | "assortment" | "offer_type"
    value: str


# Module-level cache; cleared between tests via the fixture.
_rules_cache: dict[str, Any] | None = None


def _find_rules_path() -> Path:
    """Locate ``data/tags-rules.yaml``.

    Search order:
    1. Package-relative — 4 levels up: extract → threadhunter → src → root
    2. ``$CWD/data/tags-rules.yaml`` (fallback for pip-installed CLI)
    """
    pkg_path = (
        Path(__file__).resolve().parent.parent.parent.parent
        / "data"
        / "tags-rules.yaml"
    )
    if pkg_path.is_file():
        return pkg_path

    cwd_path = Path.cwd() / "data" / "tags-rules.yaml"
    if cwd_path.is_file():
        return cwd_path

    raise FileNotFoundError(
        "tags-rules.yaml not found. Expected at data/tags-rules.yaml "
        "in the project root."
    )


def _load_rules() -> dict[str, Any]:
    """Load and cache the classification rules from YAML."""
    global _rules_cache
    if _rules_cache is not None:
        return _rules_cache

    path = _find_rules_path()
    with open(path, encoding="utf-8") as f:
        _rules_cache = yaml.safe_load(f)
    return _rules_cache


def classify_tags(text: str) -> list[ExtractedTag]:
    """Classify *text* into tags using rules from ``data/tags-rules.yaml``.

    Returns a deduplicated list sorted by ``(type, value)``.
    """
    if not text:
        return []

    rules = _load_rules()
    text_lower = text.lower()
    results: list[ExtractedTag] = []

    # Location — substring match (case-insensitive)
    for city in rules.get("location", []):
        if city.lower() in text_lower:
            results.append(ExtractedTag(type="location", value=city))

    # Assortment — keyword match (case-insensitive)
    for keyword in rules.get("assortment", []):
        if keyword.lower() in text_lower:
            results.append(ExtractedTag(type="assortment", value=keyword))

    # Offer type — pattern match (case-insensitive)
    for rule in rules.get("offer_type", []):
        pattern = rule["pattern"]
        if pattern.lower() in text_lower:
            results.append(ExtractedTag(type="offer_type", value=pattern))

    # Deduplicate
    seen: set[tuple[str, str]] = set()
    unique: list[ExtractedTag] = []
    for t in results:
        key = (t.type, t.value)
        if key not in seen:
            seen.add(key)
            unique.append(t)

    return sorted(unique, key=lambda t: (t.type, t.value))
