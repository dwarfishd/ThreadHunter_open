"""Tests for CLI add-channel and parse commands (Phase 3)."""

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.errors import ChannelPrivateError
from typer.testing import CliRunner

from threadhunter.cli import app
from threadhunter.config import reset_settings
from threadhunter.db.connection import get_connection, init_db

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path) -> Path:
    """Run tests in an isolated tmp_path."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    saved_keys = {
        k: os.environ.pop(k, None)
        for k in ("API_ID", "API_HASH", "SESSION_NAME", "TH_DB", "TH_SESSION")
        if os.environ.get(k) is not None
    }
    saved_keys = {k: v for k, v in saved_keys.items() if v is not None}

    # Create .env with valid credentials
    env_file = tmp_path / ".env"
    env_file.write_text(
        "API_ID=12345\nAPI_HASH=abc123\nSESSION_NAME=test\n", encoding="utf-8"
    )

    # Set up a temp DB
    db_path = tmp_path / "test.db"
    init_db(db_path)

    yield tmp_path

    os.chdir(original_cwd)
    for k, v in saved_keys.items():
        os.environ[k] = v
    reset_settings()


def _make_message(
    msg_id: int,
    text: str,
    date: datetime,
    has_photo: bool = False,
) -> MagicMock:
    """Create a mock Telegram Message."""
    msg = MagicMock()
    msg.id = msg_id
    msg.text = text
    msg.message = None
    msg.date = date
    msg.photo = MagicMock() if has_photo else None
    return msg


class TestAddChannel:
    """Tests for 'th add-channel' command."""

    def test_add_channel_success(self, tmp_path: Path) -> None:
        """add-channel resolves entity and saves to DB."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        mock_entity = MagicMock(title="Test Channel")

        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        db_path = tmp_path / "test.db"
        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            result = runner.invoke(app, ["add-channel", "@testchannel"])

        assert result.exit_code == 0
        assert "added" in result.output.lower() or "Test Channel" in result.output

    def test_add_channel_private(self, tmp_path: Path) -> None:
        """add-channel with private channel exits with code 1."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(
            side_effect=ChannelPrivateError(MagicMock())
        )
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
        ):
            result = runner.invoke(app, ["add-channel", "@private"])

        assert result.exit_code == 1
        assert "private" in result.output.lower() or "error" in result.output.lower()

    def test_add_channel_no_session(self, tmp_path: Path) -> None:
        """add-channel without session file exits with code 1."""
        with patch(
            "threadhunter.cli.get_session_path",
            return_value=tmp_path / "nonexistent.session",
        ):
            result = runner.invoke(app, ["add-channel", "@test"])

        assert result.exit_code == 1

    def test_add_channel_empty_name(self) -> None:
        """add-channel with empty name raises BadParameter."""
        result = runner.invoke(app, ["add-channel", "  "])
        assert result.exit_code != 0


class TestParse:
    """Tests for 'th parse' command."""

    def test_parse_no_channels(self, tmp_path: Path) -> None:
        """parse with no channels shows a helpful message."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        mock_check = AsyncMock(return_value=True)

        db_path = tmp_path / "test.db"
        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", mock_check),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code == 0
        assert "no channels" in result.output.lower()

    def test_parse_saves_posts(self, tmp_path: Path) -> None:
        """parse fetches messages and saves them to DB."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        db_path = tmp_path / "test.db"

        # Pre-add a channel
        with patch(
            "threadhunter.channels.get_connection",
            side_effect=lambda: get_connection(db_path),
        ):
            from threadhunter.channels import add_channel

            add_channel(telegram_id="testchannel", name="Test")

        # Create 5 mock messages
        messages = [
            _make_message(
                msg_id=i,
                text=f"Post {i}",
                date=datetime(2026, 7, 1, 12, i),
                has_photo=(i % 2 == 0),
            )
            for i in range(1, 6)
        ]

        mock_entity = MagicMock(title="Test Channel")
        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper.get_messages = AsyncMock(return_value=messages)
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        mock_check = AsyncMock(return_value=True)

        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", mock_check),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code == 0
        assert "5 new post(s)" in result.output

        # Verify posts in DB
        conn = get_connection(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
            assert count == 5
        finally:
            conn.close()

    def test_parse_deduplication(self, tmp_path: Path) -> None:
        """Second parse does not create duplicate posts."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        db_path = tmp_path / "test.db"

        # Pre-add a channel
        with patch(
            "threadhunter.channels.get_connection",
            side_effect=lambda: get_connection(db_path),
        ):
            from threadhunter.channels import add_channel

            add_channel(telegram_id="testchannel", name="Test")

        messages = [
            _make_message(
                msg_id=1,
                text="Post 1",
                date=datetime(2026, 7, 1, 12, 0),
            )
        ]

        mock_entity = MagicMock(title="Test Channel")
        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper.get_messages = AsyncMock(return_value=messages)
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        mock_check = AsyncMock(return_value=True)

        patches = [
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", mock_check),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ]

        # First parse
        for p in patches:
            p.start()
        result1 = runner.invoke(app, ["parse"])
        for p in patches:
            p.stop()

        assert result1.exit_code == 0
        assert "1 new post(s)" in result1.output

        # Second parse — same messages, should be deduped
        # Need to reset the mock to return same messages again
        mock_wrapper2 = AsyncMock()
        mock_wrapper2.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper2.get_messages = AsyncMock(return_value=messages)
        mock_wrapper2.connect = AsyncMock()
        mock_wrapper2.disconnect = AsyncMock()
        mock_wrapper2.__aenter__ = AsyncMock(return_value=mock_wrapper2)
        mock_wrapper2.__aexit__ = AsyncMock(return_value=False)

        patches2 = [
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", AsyncMock(return_value=True)),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper2,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ]
        for p in patches2:
            p.start()
        result2 = runner.invoke(app, ["parse"])
        for p in patches2:
            p.stop()

        assert result2.exit_code == 0
        assert "0 new post(s)" in result2.output

        # Verify only 1 post in DB
        conn = get_connection(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
            assert count == 1
        finally:
            conn.close()

    def test_parse_private_channel_skipped(self, tmp_path: Path) -> None:
        """Private channel is skipped, other channels still parsed."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        db_path = tmp_path / "test.db"

        # Add two channels
        with patch(
            "threadhunter.channels.get_connection",
            side_effect=lambda: get_connection(db_path),
        ):
            from threadhunter.channels import add_channel

            add_channel(telegram_id="private_ch", name="Private")
            add_channel(telegram_id="public_ch", name="Public")

        messages = [
            _make_message(
                msg_id=1,
                text="Public post",
                date=datetime(2026, 7, 1, 12, 0),
            )
        ]

        mock_entity = MagicMock(title="Public Channel")

        call_count = 0

        async def mock_get_entity(name: str) -> MagicMock:
            nonlocal call_count
            call_count += 1
            if name == "private_ch":
                raise ChannelPrivateError(MagicMock())
            return mock_entity

        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(side_effect=mock_get_entity)
        mock_wrapper.get_messages = AsyncMock(return_value=messages)
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        mock_check = AsyncMock(return_value=True)

        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", mock_check),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code == 0
        assert "1 new post(s)" in result.output

    def test_parse_stops_at_last_parsed(self, tmp_path: Path) -> None:
        """Pagination stops when posts are older than last_parsed."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        db_path = tmp_path / "test.db"

        # Add channel with last_parsed set
        with patch(
            "threadhunter.channels.get_connection",
            side_effect=lambda: get_connection(db_path),
        ):
            from threadhunter.channels import add_channel, update_last_parsed

            ch = add_channel(telegram_id="testchannel", name="Test")
            update_last_parsed(ch.id, datetime(2026, 7, 1, 12, 0))  # type: ignore[arg-type]

        # Messages: one newer, one older than last_parsed
        messages = [
            _make_message(
                msg_id=10,
                text="New post",
                date=datetime(2026, 7, 1, 13, 0),
            ),
            _make_message(
                msg_id=9,
                text="Old post",
                date=datetime(2026, 7, 1, 11, 0),
            ),
        ]

        mock_entity = MagicMock(title="Test Channel")
        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper.get_messages = AsyncMock(return_value=messages)
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        mock_check = AsyncMock(return_value=True)

        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", mock_check),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code == 0
        assert "1 new post(s)" in result.output

        # Verify only the new post was saved
        conn = get_connection(db_path)
        try:
            count = conn.execute("SELECT COUNT(*) FROM posts").fetchone()[0]
            assert count == 1
            row = conn.execute(
                "SELECT raw_text FROM posts LIMIT 1"
            ).fetchone()
            assert row["raw_text"] == "New post"
        finally:
            conn.close()

    def test_first_call_has_no_offset(self, tmp_path: Path) -> None:
        """First get_messages call must NOT use offset_date — Telethon
        offset_date returns messages *older* than the date, so passing
        last_parsed would skip all new messages."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        db_path = tmp_path / "test.db"

        with patch(
            "threadhunter.channels.get_connection",
            side_effect=lambda: get_connection(db_path),
        ):
            from threadhunter.channels import add_channel, update_last_parsed

            ch = add_channel(telegram_id="testchannel", name="Test")
            update_last_parsed(ch.id, datetime(2026, 7, 1, 12, 0))  # type: ignore[arg-type]

        messages = [
            _make_message(
                msg_id=10,
                text="New post",
                date=datetime(2026, 7, 1, 13, 0),
            ),
        ]

        mock_entity = MagicMock(title="Test Channel")
        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper.get_messages = AsyncMock(return_value=messages)
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", AsyncMock(return_value=True)),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            runner.invoke(app, ["parse"])

        # Verify first call was made WITHOUT offset_date
        first_call_kwargs = mock_wrapper.get_messages.call_args_list[0]
        _, kwargs = first_call_kwargs
        assert "offset_date" not in kwargs or kwargs.get("offset_date") is None

    def test_pagination_uses_composite_cursor(self, tmp_path: Path) -> None:
        """When first batch is full (100 messages), second call must use
        both offset_date AND offset_id from the oldest message."""
        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        db_path = tmp_path / "test.db"

        with patch(
            "threadhunter.channels.get_connection",
            side_effect=lambda: get_connection(db_path),
        ):
            from threadhunter.channels import add_channel

            add_channel(telegram_id="testchannel", name="Test")

        # First batch: exactly 100 messages (triggers pagination)
        batch1 = [
            _make_message(
                msg_id=200 - i,
                text=f"Post {200 - i}",
                date=datetime(2026, 7, 1, 12, 0, 0, i),
            )
            for i in range(100)
        ]
        # Second batch: 10 older messages
        batch2 = [
            _make_message(
                msg_id=50 - i,
                text=f"Old {50 - i}",
                date=datetime(2026, 6, 30, 12, 0, 0, i),
            )
            for i in range(10)
        ]

        mock_entity = MagicMock(title="Test Channel")
        mock_wrapper = AsyncMock()
        mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
        mock_wrapper.get_messages = AsyncMock(side_effect=[batch1, batch2])
        mock_wrapper.connect = AsyncMock()
        mock_wrapper.disconnect = AsyncMock()
        mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
        mock_wrapper.__aexit__ = AsyncMock(return_value=False)

        with (
            patch("threadhunter.cli.get_session_path", return_value=session_file),
            patch("threadhunter.cli.check_session", AsyncMock(return_value=True)),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper,
            ),
            patch(
                "threadhunter.channels.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
            patch(
                "threadhunter.posts.get_connection",
                side_effect=lambda: get_connection(db_path),
            ),
        ):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code == 0
        assert "110 new post(s)" in result.output

        # Verify second call used composite cursor from oldest message
        second_call = mock_wrapper.get_messages.call_args_list[1]
        _, kwargs = second_call
        assert kwargs["offset_date"] == batch1[-1].date
        assert kwargs["offset_id"] == batch1[-1].id
