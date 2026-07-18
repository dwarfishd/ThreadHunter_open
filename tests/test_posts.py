"""Tests for posts CRUD operations."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from threadhunter.channels import add_channel
from threadhunter.db.connection import get_connection, init_db
from threadhunter.posts import count_posts_by_channel, get_latest_post_date, insert_post


@pytest.fixture(autouse=True)
def db(tmp_path: Path):
    """Set up a temporary database and patch get_connection."""
    db_path = tmp_path / "test.db"
    init_db(db_path)

    with (
        patch("threadhunter.posts.get_connection") as mock_gc_posts,
        patch("threadhunter.channels.get_connection") as mock_gc_channels,
    ):
        mock_gc_posts.side_effect = lambda: get_connection(db_path)
        mock_gc_channels.side_effect = lambda: get_connection(db_path)
        yield db_path


class TestInsertPost:
    """Tests for insert_post()."""

    def test_insert_new_post(self) -> None:
        """insert_post returns True for a new post."""
        ch = add_channel(telegram_id="ch1")
        result = insert_post(
            channel_id=ch.id,  # type: ignore[arg-type]
            telegram_post_id="100",
            raw_text="Hello world",
            published_at=datetime(2026, 7, 1),
            has_photo=False,
        )
        assert result is True

    def test_insert_duplicate_returns_false(self) -> None:
        """insert_post returns False for duplicate telegram_post_id."""
        ch = add_channel(telegram_id="ch1")
        insert_post(
            channel_id=ch.id,  # type: ignore[arg-type]
            telegram_post_id="200",
            raw_text="First",
            published_at=datetime(2026, 7, 1),
            has_photo=False,
        )
        result = insert_post(
            channel_id=ch.id,  # type: ignore[arg-type]
            telegram_post_id="200",
            raw_text="Duplicate",
            published_at=datetime(2026, 7, 1),
            has_photo=False,
        )
        assert result is False

    def test_insert_post_with_photo(self) -> None:
        """insert_post stores has_photo correctly."""
        ch = add_channel(telegram_id="ch1")
        insert_post(
            channel_id=ch.id,  # type: ignore[arg-type]
            telegram_post_id="300",
            raw_text="Photo post",
            published_at=datetime(2026, 7, 1),
            has_photo=True,
        )
        conn = get_connection()
        try:
            row = conn.execute(
                "SELECT has_photo FROM posts WHERE telegram_post_id = '300'"
            ).fetchone()
            assert row["has_photo"] == 1
        finally:
            conn.close()


class TestGetLatestPostDate:
    """Tests for get_latest_post_date()."""

    def test_no_posts(self) -> None:
        """Returns None when channel has no posts."""
        ch = add_channel(telegram_id="ch1")
        assert get_latest_post_date(ch.id) is None  # type: ignore[arg-type]

    def test_returns_latest_date(self) -> None:
        """Returns the most recent published_at."""
        ch = add_channel(telegram_id="ch1")
        insert_post(
            channel_id=ch.id,  # type: ignore[arg-type]
            telegram_post_id="1",
            raw_text="Old",
            published_at=datetime(2026, 1, 1),
            has_photo=False,
        )
        insert_post(
            channel_id=ch.id,  # type: ignore[arg-type]
            telegram_post_id="2",
            raw_text="New",
            published_at=datetime(2026, 6, 1),
            has_photo=False,
        )
        latest = get_latest_post_date(ch.id)  # type: ignore[arg-type]
        assert latest is not None
        assert latest.month == 6


class TestCountPostsByChannel:
    """Tests for count_posts_by_channel()."""

    def test_no_posts(self) -> None:
        """Returns 0 when channel has no posts."""
        ch = add_channel(telegram_id="ch1")
        assert count_posts_by_channel(ch.id) == 0  # type: ignore[arg-type]

    def test_counts_posts(self) -> None:
        """Returns correct count."""
        ch = add_channel(telegram_id="ch1")
        for i in range(5):
            insert_post(
                channel_id=ch.id,  # type: ignore[arg-type]
                telegram_post_id=str(1000 + i),
                raw_text=f"Post {i}",
                published_at=datetime(2026, 7, 1),
                has_photo=False,
            )
        assert count_posts_by_channel(ch.id) == 5  # type: ignore[arg-type]
