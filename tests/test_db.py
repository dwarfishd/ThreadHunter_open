"""Tests for database schema initialization."""

import sqlite3
from pathlib import Path

from threadhunter.db.connection import get_connection, init_db


def _table_names(conn: sqlite3.Connection) -> set[str]:
    """Return set of user table names in the database."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


def _index_names(conn: sqlite3.Connection) -> set[str]:
    """Return set of user index names in the database."""
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    ).fetchall()
    return {row["name"] for row in rows}


EXPECTED_TABLES = {"channels", "posts", "contacts", "tags", "post_contacts"}
EXPECTED_INDEXES = {
    "idx_posts_telegram_post_id",
    "idx_posts_channel_id",
    "idx_tags_value",
    "idx_contacts_value",
    "idx_posts_published_at",
}


def test_init_db_creates_tables(tmp_path: Path) -> None:
    """After init_db, database contains exactly 4 expected tables."""
    db_path = tmp_path / "test.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        tables = _table_names(conn)
        assert tables == EXPECTED_TABLES, f"Expected {EXPECTED_TABLES}, got {tables}"
    finally:
        conn.close()


def test_init_db_creates_indexes(tmp_path: Path) -> None:
    """After init_db, database contains all expected indexes."""
    db_path = tmp_path / "test.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        indexes = _index_names(conn)
        expected = EXPECTED_INDEXES
        assert indexes == expected, f"Expected {expected}, got {indexes}"
    finally:
        conn.close()


def test_init_db_is_idempotent(tmp_path: Path) -> None:
    """Running init_db twice does not error (IF NOT EXISTS)."""
    db_path = tmp_path / "test.db"
    init_db(db_path)
    init_db(db_path)  # should not raise

    conn = get_connection(db_path)
    try:
        tables = _table_names(conn)
        assert tables == EXPECTED_TABLES
    finally:
        conn.close()


def test_get_connection_foreign_keys(tmp_path: Path) -> None:
    """get_connection enables foreign key enforcement."""
    db_path = tmp_path / "test.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        row = conn.execute("PRAGMA foreign_keys").fetchone()
        assert row[0] == 1
    finally:
        conn.close()


def test_get_connection_row_factory(tmp_path: Path) -> None:
    """get_connection returns connections with sqlite3.Row as row_factory."""
    db_path = tmp_path / "test.db"
    init_db(db_path)

    conn = get_connection(db_path)
    try:
        assert conn.row_factory is sqlite3.Row
    finally:
        conn.close()


def test_get_connection_rejects_file_as_parent(tmp_path: Path) -> None:
    """get_connection raises ValueError if parent path is a file."""
    fake_parent = tmp_path / "not_a_dir"
    fake_parent.write_text("blocking file")

    db_path = fake_parent / "db.sqlite"
    try:
        get_connection(db_path)
    except ValueError as e:
        assert "not a directory" in str(e)
