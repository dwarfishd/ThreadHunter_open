"""Tests for TelegramClientWrapper."""

from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
)

from threadhunter.telegram.client import TelegramClientWrapper


def _make_mock_client() -> AsyncMock:
    """Create a mock TelegramClient with standard async methods."""
    mock = AsyncMock()
    mock.connect = AsyncMock()
    mock.disconnect = AsyncMock()
    mock.get_messages = AsyncMock(return_value=[])
    mock.get_entity = AsyncMock(return_value=MagicMock(title="Test"))
    return mock


class TestContextManager:
    """Tests for async context manager protocol."""

    async def test_connect_and_disconnect(self, tmp_path: Path) -> None:
        """__aenter__ connects, __aexit__ disconnects."""
        mock_client = _make_mock_client()

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            async with TelegramClientWrapper(
                session_path=tmp_path / "test.session",
                api_id=12345,
                api_hash="abc",
            ) as wrapper:
                assert wrapper._client is not None

        mock_client.connect.assert_awaited_once()
        mock_client.disconnect.assert_awaited_once()


class TestGetEntity:
    """Tests for get_entity()."""

    async def test_get_entity_success(self, tmp_path: Path) -> None:
        """get_entity resolves a channel name."""
        mock_client = _make_mock_client()
        mock_client.get_entity = AsyncMock(
            return_value=MagicMock(title="My Channel")
        )

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            async with TelegramClientWrapper(
                session_path=tmp_path / "test.session",
                api_id=12345,
                api_hash="abc",
            ) as wrapper:
                entity = await wrapper.get_entity("@mychannel")

        assert entity.title == "My Channel"
        mock_client.get_entity.assert_awaited_once_with("@mychannel")

    async def test_get_entity_private_channel(self, tmp_path: Path) -> None:
        """get_entity raises ChannelPrivateError for private channels."""
        mock_client = _make_mock_client()
        mock_client.get_entity = AsyncMock(
            side_effect=ChannelPrivateError(MagicMock())
        )

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            async with TelegramClientWrapper(
                session_path=tmp_path / "test.session",
                api_id=12345,
                api_hash="abc",
            ) as wrapper:
                with pytest.raises(ChannelPrivateError):
                    await wrapper.get_entity("@private")


class TestGetMessages:
    """Tests for get_messages()."""

    async def test_get_messages_returns_list(self, tmp_path: Path) -> None:
        """get_messages returns a list of Message objects."""
        msg1 = MagicMock()
        msg1.id = 1
        msg1.text = "Hello"
        msg1.date = datetime(2026, 7, 1)

        mock_client = _make_mock_client()
        mock_client.get_messages = AsyncMock(return_value=[msg1])

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            async with TelegramClientWrapper(
                session_path=tmp_path / "test.session",
                api_id=12345,
                api_hash="abc",
            ) as wrapper:
                messages = await wrapper.get_messages("entity", limit=50)

        assert len(messages) == 1
        assert messages[0].text == "Hello"

    async def test_get_messages_with_offset(self, tmp_path: Path) -> None:
        """get_messages passes offset_date and offset_id to the underlying client."""
        mock_client = _make_mock_client()
        mock_client.get_messages = AsyncMock(return_value=[])

        offset = datetime(2026, 6, 1)

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            async with TelegramClientWrapper(
                session_path=tmp_path / "test.session",
                api_id=12345,
                api_hash="abc",
            ) as wrapper:
                await wrapper.get_messages(
                    "entity", limit=100, offset_date=offset, offset_id=42
                )

        mock_client.get_messages.assert_awaited_once_with(
            "entity", limit=100, offset_date=offset, offset_id=42
        )


class TestRetryLogic:
    """Tests for retry / backoff behaviour."""

    async def test_flood_wait_retries(self, tmp_path: Path) -> None:
        """FloodWaitError triggers sleep + retry."""
        mock_client = _make_mock_client()
        flood = FloodWaitError(MagicMock())
        flood.seconds = 1

        mock_client.get_entity = AsyncMock(
            side_effect=[flood, MagicMock(title="OK")]
        )

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            sleep_path = "threadhunter.telegram.client.asyncio.sleep"
            with patch(sleep_path, new_callable=AsyncMock) as mock_sleep:
                async with TelegramClientWrapper(
                    session_path=tmp_path / "test.session",
                    api_id=12345,
                    api_hash="abc",
                ) as wrapper:
                    entity = await wrapper.get_entity("@test")

        assert entity.title == "OK"
        mock_sleep.assert_awaited_once_with(1)

    async def test_network_error_retries(self, tmp_path: Path) -> None:
        """OSError triggers retry with exponential backoff."""
        mock_client = _make_mock_client()
        mock_client.get_entity = AsyncMock(
            side_effect=[OSError("timeout"), MagicMock(title="OK")]
        )

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            sleep_path = "threadhunter.telegram.client.asyncio.sleep"
            with patch(sleep_path, new_callable=AsyncMock) as mock_sleep:
                async with TelegramClientWrapper(
                    session_path=tmp_path / "test.session",
                    api_id=12345,
                    api_hash="abc",
                ) as wrapper:
                    entity = await wrapper.get_entity("@test")

        assert entity.title == "OK"
        mock_sleep.assert_awaited_once_with(1.0)

    async def test_max_retries_exceeded(self, tmp_path: Path) -> None:
        """After MAX_RETRIES failures, the last exception is raised."""
        mock_client = _make_mock_client()
        mock_client.get_entity = AsyncMock(
            side_effect=OSError("timeout")
        )

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            sleep_path = "threadhunter.telegram.client.asyncio.sleep"
            with patch(sleep_path, new_callable=AsyncMock):
                async with TelegramClientWrapper(
                    session_path=tmp_path / "test.session",
                    api_id=12345,
                    api_hash="abc",
                ) as wrapper:
                    with pytest.raises(OSError):
                        await wrapper.get_entity("@test")

    async def test_channel_private_not_retried(self, tmp_path: Path) -> None:
        """ChannelPrivateError is raised immediately, no retry."""
        mock_client = _make_mock_client()
        mock_client.get_entity = AsyncMock(
            side_effect=ChannelInvalidError(MagicMock())
        )

        with patch(
            "threadhunter.telegram.client.TelegramClient",
            return_value=mock_client,
        ):
            async with TelegramClientWrapper(
                session_path=tmp_path / "test.session",
                api_id=12345,
                api_hash="abc",
            ) as wrapper:
                with pytest.raises(ChannelInvalidError):
                    await wrapper.get_entity("@invalid")
