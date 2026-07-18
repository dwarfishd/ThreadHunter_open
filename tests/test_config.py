"""Tests for configuration loading and validation."""

import logging
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from threadhunter.config import (
    Settings,
    get_settings,
    load_config,
    reset_settings,
)


@pytest.fixture(autouse=True)
def _reset_settings_between_tests() -> None:
    """Reset global settings before and after each test."""
    reset_settings()
    yield
    reset_settings()


# --- Settings model tests ---


class TestSettings:
    """Tests for the Settings Pydantic model."""

    def test_valid_full_config(self) -> None:
        """Settings with api_id and api_hash passes validation."""
        s = Settings(api_id=12345, api_hash="abc123")
        assert s.api_id == 12345
        assert s.api_hash == "abc123"
        assert s.has_telegram_credentials is True

    def test_api_id_as_string_converted(self) -> None:
        """api_id accepts a string and converts to int."""
        s = Settings(api_id="12345")
        assert s.api_id == 12345

    def test_api_id_invalid_string_raises(self) -> None:
        """api_id rejects non-numeric strings."""
        with pytest.raises(Exception):  # pydantic.ValidationError
            Settings(api_id="not-a-number")

    def test_empty_api_id_is_none(self) -> None:
        """Empty string api_id becomes None."""
        s = Settings(api_id="")
        assert s.api_id is None

    def test_empty_api_hash_is_none(self) -> None:
        """Empty string api_hash becomes None."""
        s = Settings(api_hash="")
        assert s.api_hash is None

    def test_whitespace_only_api_hash_is_none(self) -> None:
        """Whitespace-only api_hash becomes None."""
        s = Settings(api_hash="   ")
        assert s.api_hash is None

    def test_missing_credentials(self) -> None:
        """Settings without api_id/api_hash has has_telegram_credentials=False."""
        s = Settings()
        assert s.has_telegram_credentials is False

    def test_partial_credentials(self) -> None:
        """Only api_id without api_hash → has_telegram_credentials=False."""
        s = Settings(api_id=12345)
        assert s.has_telegram_credentials is False

    def test_default_session_name(self) -> None:
        """session_name defaults to 'threadhunter'."""
        s = Settings()
        assert s.session_name == "threadhunter"

    def test_custom_session_name(self) -> None:
        """session_name can be set explicitly."""
        s = Settings(session_name="custom_session")
        assert s.session_name == "custom_session"


# --- load_config tests ---


class TestLoadConfig:
    """Tests for the load_config function."""

    def test_load_config_without_env_file(self, tmp_path: Path) -> None:
        """load_config works without .env file (uses env vars / defaults)."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("threadhunter.config._find_env_file", return_value=None):
                settings = load_config()
                assert settings.api_id is None
                assert settings.api_hash is None
                assert settings.session_name == "threadhunter"

    def test_load_config_warns_on_missing_api_id(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """load_config logs a warning when API_ID is not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("threadhunter.config._find_env_file", return_value=None):
                with caplog.at_level(logging.WARNING, logger="threadhunter"):
                    load_config()
                assert any(
                    "API_ID is not set" in record.message for record in caplog.records
                )

    def test_load_config_warns_on_missing_api_hash(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """load_config logs a warning when API_HASH is not set."""
        with patch.dict(os.environ, {"API_ID": "12345"}, clear=True):
            with patch("threadhunter.config._find_env_file", return_value=None):
                with caplog.at_level(logging.WARNING, logger="threadhunter"):
                    load_config()
                assert any(
                    "API_HASH is not set" in record.message for record in caplog.records
                )

    def test_load_config_from_env(self) -> None:
        """load_config reads from environment variables."""
        with patch.dict(
            os.environ,
            {"API_ID": "99999", "API_HASH": "testhash", "SESSION_NAME": "mysession"},
            clear=True,
        ):
            with patch("threadhunter.config._find_env_file", return_value=None):
                settings = load_config()
                assert settings.api_id == 99999
                assert settings.api_hash == "testhash"
                assert settings.session_name == "mysession"

    def test_load_config_invalid_api_id_raises(self) -> None:
        """load_config raises on invalid API_ID (non-integer)."""
        with patch.dict(os.environ, {"API_ID": "not-an-int"}, clear=True):
            with patch("threadhunter.config._find_env_file", return_value=None):
                with pytest.raises(Exception):  # pydantic.ValidationError
                    load_config()

    def test_get_settings_loads_if_not_set(self) -> None:
        """get_settings calls load_config if settings not yet loaded."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("threadhunter.config._find_env_file", return_value=None):
                settings = get_settings()
                assert isinstance(settings, Settings)
