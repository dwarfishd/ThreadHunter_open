"""Pipeline orchestrator: extract contacts + classify tags → store in DB.

Contains **only flow control**.  Business logic lives in ``extract/*``.
"""

from __future__ import annotations

import logging
import sqlite3

from threadhunter.db import get_connection
from threadhunter.extract.contacts import extract_contacts
from threadhunter.extract.tags import classify_tags

logger = logging.getLogger(__name__)

__all__ = ["process_channel", "process_post", "run_pipeline"]

_FETCH_BATCH = 1000


def process_post(
    post_id: int,
    raw_text: str | None,
    _conn: sqlite3.Connection | None = None,
) -> None:
    """Extract contacts and classify tags for a single post, store in DB.

    Uses INSERT OR IGNORE so re-processing is idempotent.
    Pass *_conn* to reuse an existing connection (caller manages commit).
    """
    if not raw_text:
        return

    own_conn = _conn is None
    conn = _conn or get_connection()
    try:
        contacts = extract_contacts(raw_text)
        for c in contacts:
            conn.execute(
                "INSERT OR IGNORE INTO contacts (type, value, post_id) "
                "VALUES (?, ?, ?)",
                (c.type, c.value, post_id),
            )

        tags = classify_tags(raw_text)
        for t in tags:
            conn.execute(
                "INSERT OR IGNORE INTO tags (type, value, post_id) "
                "VALUES (?, ?, ?)",
                (t.type, t.value, post_id),
            )

        if own_conn:
            conn.commit()
        logger.debug(
            "Post %d: %d contact(s), %d tag(s)",
            post_id,
            len(contacts),
            len(tags),
        )
    finally:
        if own_conn:
            conn.close()


def _ensure_processed_at(conn: sqlite3.Connection) -> None:
    """Add ``processed_at`` column if the database was created before Phase 4."""
    cols = {
        row["name"]
        for row in conn.execute("PRAGMA table_info(posts)").fetchall()
    }
    if "processed_at" not in cols:
        conn.execute(
            "ALTER TABLE posts ADD COLUMN processed_at DATETIME"
        )
        conn.commit()


def process_channel(channel_id: int) -> int:
    """Process only unprocessed posts for a channel.

    Returns count of newly processed posts.  Uses a single connection with
    cursor-based pagination and one transaction per batch.
    """
    conn = get_connection()
    try:
        _ensure_processed_at(conn)

        cursor = conn.execute(
            "SELECT id, raw_text FROM posts "
            "WHERE channel_id = ? AND processed_at IS NULL",
            (channel_id,),
        )
        count = 0
        while True:
            rows = cursor.fetchmany(_FETCH_BATCH)
            if not rows:
                break
            processed_ids: list[int] = []
            for row in rows:
                try:
                    process_post(row["id"], row["raw_text"], _conn=conn)
                    processed_ids.append(row["id"])
                    count += 1
                except Exception:
                    logger.warning(
                        "Failed to process post %d", row["id"], exc_info=True
                    )
            if processed_ids:
                conn.executemany(
                    "UPDATE posts SET processed_at = datetime('now') "
                    "WHERE id = ?",
                    [(pid,) for pid in processed_ids],
                )
            conn.commit()
    finally:
        conn.close()

    logger.info("Channel %d: processed %d new post(s)", channel_id, count)
    return count


def run_pipeline() -> int:
    """Run extraction pipeline for all channels. Returns total processed."""
    from threadhunter.channels import list_channels

    channels = list_channels()
    total = 0
    for ch in channels:
        if ch.id is None:
            continue
        try:
            total += process_channel(ch.id)
        except Exception:
            logger.warning(
                "Failed to process channel %d", ch.id, exc_info=True
            )
    logger.info("Pipeline complete: %d post(s) processed", total)
    return total
