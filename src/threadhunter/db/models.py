"""Pydantic models for ThreadHunter database entities."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Channel(BaseModel):
    """Represents a Telegram channel being watched."""

    id: Optional[int] = None
    telegram_id: str
    name: Optional[str] = None
    added_at: Optional[datetime] = None
    last_parsed: Optional[datetime] = None


class Post(BaseModel):
    """Represents a parsed Telegram post."""

    id: Optional[int] = None
    channel_id: int
    telegram_post_id: str
    raw_text: Optional[str] = None
    published_at: Optional[datetime] = None
    parsed_at: Optional[datetime] = None
    has_photo: bool = False
    status: str = Field(default="active", pattern="^(active|closed)$")


class Contact(BaseModel):
    """Represents a contact extracted from a post."""

    id: Optional[int] = None
    post_id: int
    type: str = Field(pattern="^(phone|telegram|email|name)$")
    value: str


class Tag(BaseModel):
    """Represents a classification tag on a post."""

    id: Optional[int] = None
    post_id: int
    type: str = Field(pattern="^(location|assortment|offer_type)$")
    value: str
