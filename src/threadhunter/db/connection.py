"""Database connection management for ThreadHunter."""

import os
import sqlite3
from pathlib import Path
from typing import Optional

__all__ = ["get_connection", "get_db_path", "init_db"]


DEFAULT_DB_NAME = "threadhunter.db"


def get_db_path() -> Path:
    """Return the path to the SQLite database.

    Uses TH_DB environment variable if set, otherwise defaults to
    ~/.threadhunter/threadhunter.db.
    """
    env_path = os.environ.get("TH_DB")
    if env_path:
        return Path(env_path)
    return Path.home() / ".threadhunter" / DEFAULT_DB_NAME


def _ensure_path(db_path: Path) -> None:
    """Ensure the database path is valid and parent directory exists."""
    parent = db_path.parent
    if parent.exists() and not parent.is_dir():
        raise ValueError(
            f"Database parent path exists but is not a directory: {parent}"
        )
    parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists() and not db_path.is_file():
        raise ValueError(
            f"Database path exists but is not a file: {db_path}"
        )


def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Return a sqlite3 connection with row_factory and foreign keys.

    Creates parent directories if they don't exist.
    """
    path = db_path or get_db_path()
    _ensure_path(path)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db(db_path: Optional[Path] = None) -> None:
    """Execute schema.sql to create tables and indexes if they don't exist."""
    schema_path = Path(__file__).parent / "schema.sql"
    sql = schema_path.read_text(encoding="utf-8")

    conn = get_connection(db_path)
    try:
        conn.executescript(sql)
        conn.commit()
    finally:
        conn.close()
