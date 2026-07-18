"""Extraction package: contacts and tags extraction from post text."""

from threadhunter.extract.contacts import ExtractedContact, extract_contacts
from threadhunter.extract.tags import ExtractedTag, classify_tags

__all__ = [
    "ExtractedContact",
    "ExtractedTag",
    "classify_tags",
    "extract_contacts",
]
