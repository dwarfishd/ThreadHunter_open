"""Tests for channels CRUD operations."""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from threadhunter.channels import (
    add_channel,
    get_channel_by_id,
    list_channels,
    update_last_parsed,
)
from threadhunter.db.connection import get_connection, init_db


@pytest.fixture(autouse=True)
def db(tmp_path: Path):
    """Set up a temporary database and patch get_connection."""
    db_path = tmp_path / "test.db"
    init_db(db_path)

    with patch("threadhunter.channels.get_connection") as mock_gc:
        mock_gc.side_effect = lambda: get_connection(db_path)
        yield db_path


class TestAddChannel:
    """Tests for add_channel()."""

    def test_add_new_channel(self) -> None:
        """add_channel inserts a new row and returns it."""
        ch = add_channel(telegram_id="testchannel", name="Test Channel")
        assert ch.id is not None
        assert ch.telegram_id == "testchannel"
        assert ch.name == "Test Channel"
        assert ch.last_parsed is None

    def test_add_duplicate_channel_returns_existing(self) -> None:
        """Adding a duplicate telegram_id returns the existing row."""
        ch1 = add_channel(telegram_id="dup", name="First")
        ch2 = add_channel(telegram_id="dup", name="Second")
        assert ch1.id == ch2.id
        assert ch2.name == "First"  # name not updated on duplicate

    def test_add_channel_without_name(self) -> None:
        """add_channel works with name=None."""
        ch = add_channel(telegram_id="noname")
        assert ch.name is None


class TestListChannels:
    """Tests for list_channels()."""

    def test_empty_database(self) -> None:
        """list_channels returns empty list when no channels."""
        assert list_channels() == []

    def test_returns_all_channels(self) -> None:
        """list_channels returns all added channels."""
        add_channel(telegram_id="ch1", name="A")
        add_channel(telegram_id="ch2", name="B")
        channels = list_channels()
        assert len(channels) == 2
        ids = {ch.telegram_id for ch in channels}
        assert ids == {"ch1", "ch2"}


class TestGetChannelById:
    """Tests for get_channel_by_id()."""

    def test_existing_channel(self) -> None:
        """get_channel_by_id returns the channel."""
        ch = add_channel(telegram_id="findme", name="Find Me")
        found = get_channel_by_id(ch.id)  # type: ignore[arg-type]
        assert found is not None
        assert found.telegram_id == "findme"

    def test_nonexistent_channel(self) -> None:
        """get_channel_by_id returns None for missing id."""
        assert get_channel_by_id(99999) is None


class TestUpdateLastParsed:
    """Tests for update_last_parsed()."""

    def test_update_timestamp(self) -> None:
        """update_last_parsed sets the last_parsed field."""
        ch = add_channel(telegram_id="ts_test")
        ts = datetime(2026, 7, 1, 12, 0, 0)
        update_last_parsed(ch.id, ts)  # type: ignore[arg-type]

        updated = get_channel_by_id(ch.id)  # type: ignore[arg-type]
        assert updated is not None
        assert updated.last_parsed is not None
        assert updated.last_parsed.year == 2026
