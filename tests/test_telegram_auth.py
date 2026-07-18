"""Tests for Telegram authorization flow."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from telethon.errors import CodeInvalidError

from threadhunter.telegram.auth import (
    _session_cache,
    check_session,
    get_session_path,
    start_auth,
)


@pytest.fixture(autouse=True)
def _clear_session_cache():
    """Clear session cache before each test."""
    _session_cache.clear()
    yield
    _session_cache.clear()


class TestGetSessionPath:
    """Tests for session path resolution."""

    def test_default_session_path(self) -> None:
        """Default session path is ~/.threadhunter/threadhunter.session."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove TH_SESSION if set
            os.environ.pop("TH_SESSION", None)
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.session_name = "threadhunter"
                path = get_session_path()
        assert path == Path.home() / ".threadhunter" / "threadhunter.session"

    def test_th_session_env_override(self) -> None:
        """TH_SESSION env var overrides default path."""
        custom_path = "/tmp/custom/session.session"
        with patch.dict(os.environ, {"TH_SESSION": custom_path}):
            path = get_session_path()
        assert path == Path(custom_path)

    def test_custom_session_name(self) -> None:
        """Custom session_name produces correct path."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("TH_SESSION", None)
            path = get_session_path(session_name="mybot")
        assert path == Path.home() / ".threadhunter" / "mybot.session"


class TestStartAuth:
    """Tests for start_auth() with mocked TelegramClient."""

    async def test_successful_auth(self, tmp_path: Path) -> None:
        """Successful authorization creates session file."""
        session_path = tmp_path / "test.session"

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client.send_code_request = AsyncMock()
        mock_client.sign_in = AsyncMock()
        mock_client.session = MagicMock()
        mock_client.session.save = AsyncMock()
        mock_client.disconnect = AsyncMock()

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            result = await start_auth(
                phone="+996555123456",
                session_path=session_path,
                code="12345",
                api_id=12345,
                api_hash="abc123",
            )

        assert result == session_path
        assert session_path.parent.exists()
        mock_client.connect.assert_awaited_once()
        mock_client.send_code_request.assert_awaited_once_with("+996555123456")
        mock_client.sign_in.assert_awaited_once_with("+996555123456", "12345")
        mock_client.session.save.assert_awaited_once()
        mock_client.disconnect.assert_awaited_once()

    async def test_auth_code_invalid(self, tmp_path: Path) -> None:
        """CodeInvalidError is raised when code is wrong."""
        session_path = tmp_path / "test.session"

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client.send_code_request = AsyncMock()
        mock_client.sign_in = AsyncMock(
            side_effect=CodeInvalidError(MagicMock())
        )
        mock_client.disconnect = AsyncMock()

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            with pytest.raises(CodeInvalidError):
                await start_auth(
                    phone="+996555123456",
                    session_path=session_path,
                    code="00000",
                    api_id=12345,
                    api_hash="abc123",
                )

        mock_client.disconnect.assert_awaited_once()

    async def test_auth_already_authorized(self, tmp_path: Path) -> None:
        """If already authorized, skip send_code_request and sign_in."""
        session_path = tmp_path / "test.session"

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.session = MagicMock()
        mock_client.session.save = AsyncMock()
        mock_client.disconnect = AsyncMock()

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            result = await start_auth(
                phone="+996555123456",
                session_path=session_path,
                code="12345",
                api_id=12345,
                api_hash="abc123",
            )

        assert result == session_path
        mock_client.send_code_request.assert_not_called()
        mock_client.sign_in.assert_not_called()
        mock_client.session.save.assert_awaited_once()


class TestCheckSession:
    """Tests for check_session() with mocked TelegramClient."""

    async def test_check_session_file_not_found(self, tmp_path: Path) -> None:
        """Returns False if session file does not exist."""
        session_path = tmp_path / "nonexistent.session"
        result = await check_session(session_path)
        assert result is False

    async def test_check_session_valid(self, tmp_path: Path) -> None:
        """Returns True for valid session."""
        session_path = tmp_path / "test.session"
        session_path.write_text("fake session data", encoding="utf-8")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.has_telegram_credentials = True
                mock_settings.return_value.api_id = 12345
                mock_settings.return_value.api_hash = "abc123"
                result = await check_session(session_path)

        assert result is True
        mock_client.connect.assert_awaited_once()
        mock_client.disconnect.assert_awaited_once()

    async def test_check_session_invalid(self, tmp_path: Path) -> None:
        """Returns False for invalid session."""
        session_path = tmp_path / "test.session"
        session_path.write_text("fake session data", encoding="utf-8")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client.disconnect = AsyncMock()

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.has_telegram_credentials = True
                mock_settings.return_value.api_id = 12345
                mock_settings.return_value.api_hash = "abc123"
                result = await check_session(session_path)

        assert result is False


class TestSessionCache:
    """Tests for session cache behavior."""

    async def test_check_session_uses_cache(self, tmp_path: Path) -> None:
        """Second check_session call uses cache (no TCP connection)."""
        session_path = tmp_path / "test.session"
        session_path.write_text("fake session data", encoding="utf-8")

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=True)
        mock_client.disconnect = AsyncMock()

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            with patch("threadhunter.config.get_settings") as mock_settings:
                mock_settings.return_value.has_telegram_credentials = True
                mock_settings.return_value.api_id = 12345
                mock_settings.return_value.api_hash = "abc123"

                # First call: cache miss
                result1 = await check_session(session_path)
                assert result1 is True
                assert mock_client.connect.await_count == 1

                # Second call: cache hit (no new connection)
                result2 = await check_session(session_path)
                assert result2 is True
                assert mock_client.connect.await_count == 1  # Still 1

    async def test_start_auth_invalidates_cache(self, tmp_path: Path) -> None:
        """start_auth invalidates cache for the session."""
        session_path = tmp_path / "test.session"

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock()
        mock_client.is_user_authorized = AsyncMock(return_value=False)
        mock_client.send_code_request = AsyncMock()
        mock_client.sign_in = AsyncMock()
        mock_client.session = MagicMock()
        mock_client.session.save = AsyncMock()
        mock_client.disconnect = AsyncMock()

        # Pre-populate cache
        _session_cache[str(session_path)] = (True, 0.0)

        with patch(
            "threadhunter.telegram.auth.TelegramClient", return_value=mock_client
        ):
            await start_auth(
                phone="+996555123456",
                session_path=session_path,
                code="12345",
                api_id=12345,
                api_hash="abc123",
            )

        # Cache should be invalidated
        assert str(session_path) not in _session_cache
