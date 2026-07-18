"""Tests for CLI commands: init, parse (fail-fast)."""

import os
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest
from typer.testing import CliRunner

from threadhunter.cli import app
from threadhunter.config import reset_settings

runner = CliRunner()


@pytest.fixture(autouse=True)
def _isolate_env(tmp_path: Path) -> Path:
    """Run tests in an isolated tmp_path so .env and env vars don't leak."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    # Save and clear relevant env vars
    saved_keys = {
        k: os.environ.pop(k, None)
        for k in ("API_ID", "API_HASH", "SESSION_NAME", "TH_DB", "TH_SESSION")
        if os.environ.get(k) is not None
    }
    saved_keys = {k: v for k, v in saved_keys.items() if v is not None}
    yield tmp_path
    os.chdir(original_cwd)
    # Restore saved env vars
    for k, v in saved_keys.items():
        os.environ[k] = v
    reset_settings()


class TestInitCommand:
    """Tests for 'th init' command."""

    def test_init_creates_env_from_template(self, tmp_path: Path) -> None:
        """th init copies .env.example to .env when .env doesn't exist."""
        env_example = tmp_path / ".env.example"
        env_example.write_text("API_ID=\nAPI_HASH=\n", encoding="utf-8")

        with patch("threadhunter.db.connection.get_db_path") as mock_db:
            mock_db.return_value = tmp_path / "test.db"
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert (tmp_path / ".env").exists()

    def test_init_does_not_overwrite_existing_env(self, tmp_path: Path) -> None:
        """th init does not overwrite an existing .env file."""
        env_file = tmp_path / ".env"
        env_example = tmp_path / ".env.example"
        env_file.write_text("API_ID=12345\n", encoding="utf-8")
        env_example.write_text("API_ID=\nAPI_HASH=\n", encoding="utf-8")

        with patch("threadhunter.db.connection.get_db_path") as mock_db:
            mock_db.return_value = tmp_path / "test.db"
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert env_file.read_text(encoding="utf-8") == "API_ID=12345\n"

    def test_init_creates_database(self, tmp_path: Path) -> None:
        """th init creates the database file with tables."""
        db_path = tmp_path / "test.db"
        env_example = tmp_path / ".env.example"
        env_example.write_text("API_ID=\nAPI_HASH=\n", encoding="utf-8")

        with patch("threadhunter.db.connection.get_db_path", return_value=db_path):
            result = runner.invoke(app, ["init"])

        assert result.exit_code == 0
        assert db_path.exists()

        import sqlite3

        conn = sqlite3.connect(str(db_path))
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
        conn.close()
        table_names = {row[0] for row in tables}
        assert {"channels", "posts", "contacts", "tags"}.issubset(table_names)


class TestParseFailFast:
    """Tests for 'th parse' fail-fast behaviour without valid config."""

    def test_parse_fails_without_api_id(self, tmp_path: Path) -> None:
        """th parse exits with error when API_ID is missing."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_ID=\nAPI_HASH=somehash\n", encoding="utf-8")

        result = runner.invoke(app, ["parse"])

        assert result.exit_code != 0

    def test_parse_fails_without_api_hash(self, tmp_path: Path) -> None:
        """th parse exits with error when API_HASH is missing."""
        env_file = tmp_path / ".env"
        env_file.write_text("API_ID=12345\nAPI_HASH=\n", encoding="utf-8")

        result = runner.invoke(app, ["parse"])

        assert result.exit_code != 0

    def test_parse_fails_without_env_file(self, tmp_path: Path) -> None:
        """th parse exits with error when no .env and no env vars set."""
        # Ensure no .env exists and clear environment
        with patch.dict(os.environ, {}, clear=True):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code != 0

    def test_parse_succeeds_with_valid_config(self, tmp_path: Path) -> None:
        """th parse proceeds when both API_ID and API_HASH are set."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "API_ID=12345\nAPI_HASH=abc123\n", encoding="utf-8"
        )

        session_file = tmp_path / "test.session"
        session_file.write_text("fake", encoding="utf-8")

        mock_check = AsyncMock(return_value=True)
        with (
            patch(
                "threadhunter.cli.get_session_path",
                return_value=session_file,
            ),
            patch(
                "threadhunter.cli.check_session",
                mock_check,
            ),
            patch(
                "threadhunter.cli.list_channels",
                return_value=[],
            ),
        ):
            result = runner.invoke(app, ["parse"])

        assert result.exit_code == 0
