"""CRUD operations for the posts table."""

import logging
from datetime import datetime
from typing import Optional

from threadhunter.db import get_connection

logger = logging.getLogger(__name__)


def insert_post(
    channel_id: int,
    telegram_post_id: str,
    raw_text: Optional[str],
    published_at: Optional[datetime],
    has_photo: bool,
) -> bool:
    """Insert a post using INSERT OR IGNORE (dedup by telegram_post_id).

    Returns True if a new row was actually inserted, False if it already
    existed.
    """
    conn = get_connection()
    try:
        cursor = conn.execute(
            "INSERT OR IGNORE INTO posts "
            "(channel_id, telegram_post_id, raw_text, published_at, has_photo) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                channel_id,
                telegram_post_id,
                raw_text,
                published_at.isoformat() if published_at else None,
                int(has_photo),
            ),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_latest_post_date(channel_id: int) -> Optional[datetime]:
    """Return the most recent ``published_at`` for a channel, or None."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT MAX(published_at) AS latest FROM posts WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()
        if row is None or row["latest"] is None:
            return None
        try:
            return datetime.fromisoformat(row["latest"])
        except (ValueError, TypeError):
            return None
    finally:
        conn.close()


def count_posts_by_channel(channel_id: int) -> int:
    """Return the number of posts for a given channel."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT COUNT(*) AS cnt FROM posts WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()
        return row["cnt"] if row else 0
    finally:
        conn.close()
