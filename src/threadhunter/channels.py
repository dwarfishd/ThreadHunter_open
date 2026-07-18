"""CRUD operations for the channels table."""

import logging
import sqlite3
from datetime import datetime
from typing import Optional

from threadhunter.db import Channel, get_connection

logger = logging.getLogger(__name__)


def add_channel(telegram_id: str, name: Optional[str] = None) -> Channel:
    """Insert a channel into the database.

    If a channel with the same ``telegram_id`` already exists the existing
    row is returned unchanged (no duplicate error).
    """
    conn = get_connection()
    try:
        conn.execute(
            "INSERT OR IGNORE INTO channels (telegram_id, name) VALUES (?, ?)",
            (telegram_id, name),
        )
        conn.commit()
        return _fetch_by_telegram_id(conn, telegram_id)
    finally:
        conn.close()


def list_channels() -> list[Channel]:
    """Return all channels ordered by ``added_at``."""
    conn = get_connection()
    try:
        rows = conn.execute(
            "SELECT id, telegram_id, name, added_at, last_parsed "
            "FROM channels ORDER BY added_at"
        ).fetchall()
        return [_row_to_channel(r) for r in rows]
    finally:
        conn.close()


def get_channel_by_id(channel_id: int) -> Optional[Channel]:
    """Return a single channel by its internal ``id``, or ``None``."""
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT id, telegram_id, name, added_at, last_parsed "
            "FROM channels WHERE id = ?",
            (channel_id,),
        ).fetchone()
        if row is None:
            return None
        return _row_to_channel(row)
    finally:
        conn.close()


def update_last_parsed(channel_id: int, timestamp: datetime) -> None:
    """Set ``last_parsed`` for a channel."""
    conn = get_connection()
    try:
        conn.execute(
            "UPDATE channels SET last_parsed = ? WHERE id = ?",
            (timestamp.isoformat(), channel_id),
        )
        conn.commit()
    finally:
        conn.close()


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------


def _fetch_by_telegram_id(conn: sqlite3.Connection, telegram_id: str) -> Channel:
    row = conn.execute(
        "SELECT id, telegram_id, name, added_at, last_parsed "
        "FROM channels WHERE telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    if row is None:
        raise RuntimeError(f"Channel not found after insert: {telegram_id}")
    return _row_to_channel(row)


def _row_to_channel(row: sqlite3.Row) -> Channel:
    return Channel(
        id=row["id"],
        telegram_id=row["telegram_id"],
        name=row["name"],
        added_at=_parse_dt(row["added_at"]),
        last_parsed=_parse_dt(row["last_parsed"]),
    )


def _parse_dt(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    try:
        return datetime.fromisoformat(value)
    except (ValueError, TypeError):
        return None
