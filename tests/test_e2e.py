"""End-to-end test: init → auth (mock) → add-channel → parse → status."""

from __future__ import annotations

import os
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from typer.testing import CliRunner

from threadhunter.cli import app
from threadhunter.config import reset_settings
from threadhunter.db.connection import get_connection, init_db

runner = CliRunner()

RULES_YAML = """\
location:
  - Бишкек
  - Москва
assortment:
  - куртки
  - футболки
offer_type:
  - pattern: "ищем"
  - pattern: "предлагаем"
"""


@pytest.fixture(autouse=True)
def _isolate(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Isolate each test in a temp directory with its own DB and .env."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    for k in ("API_ID", "API_HASH", "SESSION_NAME", "TH_DB", "TH_SESSION"):
        monkeypatch.delenv(k, raising=False)

    db_path = tmp_path / "test.db"
    monkeypatch.setenv("TH_DB", str(db_path))
    init_db(db_path)

    yield

    os.chdir(original_cwd)
    reset_settings()


@pytest.fixture(autouse=True)
def _clear_rules_cache() -> None:
    import threadhunter.extract.tags as tags_mod

    tags_mod._rules_cache = None


def _write_env(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text(
        "API_ID=12345\nAPI_HASH=abc123\nSESSION_NAME=test\n",
        encoding="utf-8",
    )


def _make_message(
    msg_id: int,
    text: str,
    date: datetime,
    has_photo: bool = False,
) -> MagicMock:
    msg = MagicMock()
    msg.id = msg_id
    msg.text = text
    msg.message = None
    msg.date = date
    msg.photo = MagicMock() if has_photo else None
    return msg


def _mock_client(
    entity_title: str = "Test Channel",
    messages: list[MagicMock] | None = None,
) -> AsyncMock:
    mock_entity = MagicMock(title=entity_title)
    mock_wrapper = AsyncMock()
    mock_wrapper.get_entity = AsyncMock(return_value=mock_entity)
    mock_wrapper.get_messages = AsyncMock(return_value=messages or [])
    mock_wrapper.connect = AsyncMock()
    mock_wrapper.disconnect = AsyncMock()
    mock_wrapper.__aenter__ = AsyncMock(return_value=mock_wrapper)
    mock_wrapper.__aexit__ = AsyncMock(return_value=False)
    return mock_wrapper


class TestE2E:
    """Full pipeline: init → auth → add-channel → parse → status."""

    def test_full_pipeline(self, tmp_path: Path) -> None:
        # --- Step 1: th init ---
        _write_env(tmp_path)
        result_init = runner.invoke(app, ["init"])
        assert result_init.exit_code == 0
        assert "initialized" in result_init.output.lower()

        # --- Step 2: th auth (mocked) ---
        session_file = tmp_path / "test.session"
        with (
            patch("threadhunter.cli.load_config") as mock_load,
            patch(
                "threadhunter.cli.get_session_path",
                return_value=session_file,
            ),
            patch(
                "threadhunter.cli.start_auth",
                new_callable=AsyncMock,
            ),
        ):
            settings = MagicMock()
            settings.has_telegram_credentials = True
            settings.api_id = 12345
            settings.api_hash = "abc123"
            settings.session_name = "test"
            mock_load.return_value = settings

            runner.invoke(
                app, ["auth"], input="+996555123456\n12345\n"
            )

        # Create session file so subsequent commands find it
        session_file.write_text("fake-session", encoding="utf-8")

        # --- Step 3: th add-channel @testchannel (mocked) ---
        mock_wrapper_add = _mock_client(entity_title="Test Channel")

        with (
            patch(
                "threadhunter.cli.get_session_path",
                return_value=session_file,
            ),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper_add,
            ),
        ):
            result_add = runner.invoke(
                app, ["add-channel", "@testchannel"]
            )

        assert result_add.exit_code == 0
        out = result_add.output.lower()
        assert "added" in out or "test channel" in out

        # Verify channel in DB
        db_path = Path(os.environ["TH_DB"])
        conn = get_connection(db_path)
        try:
            ch_count = conn.execute(
                "SELECT COUNT(*) FROM channels"
            ).fetchone()[0]
            assert ch_count == 1
            ch_row = conn.execute(
                "SELECT telegram_id, name FROM channels LIMIT 1"
            ).fetchone()
            assert ch_row["telegram_id"] == "testchannel"
        finally:
            conn.close()

        # --- Step 4: th parse (mocked) ---
        ad_text = (
            "Ищем швею для пошива курток в Бишкеке. "
            "Тел: +996 555 123 456, @factory"
        )
        messages = [
            _make_message(
                msg_id=1,
                text=ad_text,
                date=datetime(2026, 7, 1, 12, 0),
                has_photo=True,
            ),
            _make_message(
                msg_id=2,
                text="Предлагаем футболки оптом, Москва, info@textile.ru",
                date=datetime(2026, 7, 1, 13, 0),
            ),
            _make_message(
                msg_id=3,
                text="Обычный пост без контактов",
                date=datetime(2026, 7, 1, 14, 0),
            ),
        ]

        mock_wrapper_parse = _mock_client(
            entity_title="Test Channel",
            messages=messages,
        )

        # Set up rules for tag classification
        data_dir = tmp_path / "data"
        data_dir.mkdir(exist_ok=True)
        (data_dir / "tags-rules.yaml").write_text(
            RULES_YAML, encoding="utf-8"
        )

        with (
            patch(
                "threadhunter.cli.get_session_path",
                return_value=session_file,
            ),
            patch(
                "threadhunter.cli.check_session",
                new_callable=AsyncMock,
                return_value=True,
            ),
            patch(
                "threadhunter.cli.TelegramClientWrapper",
                return_value=mock_wrapper_parse,
            ),
        ):
            result_parse = runner.invoke(app, ["parse"])

        assert result_parse.exit_code == 0
        assert "3 new post(s)" in result_parse.output

        # Verify data in DB
        conn = get_connection(db_path)
        try:
            posts_count = conn.execute(
                "SELECT COUNT(*) FROM posts"
            ).fetchone()[0]
            assert posts_count == 3

            contacts_count = conn.execute(
                "SELECT COUNT(*) FROM contacts"
            ).fetchone()[0]
            assert contacts_count > 0

            tags_count = conn.execute(
                "SELECT COUNT(*) FROM tags"
            ).fetchone()[0]
            assert tags_count > 0

            ch = conn.execute(
                "SELECT last_parsed FROM channels LIMIT 1"
            ).fetchone()
            assert ch["last_parsed"] is not None
        finally:
            conn.close()

        # --- Step 5: th status ---
        result_status = runner.invoke(app, ["status"])
        assert result_status.exit_code == 0
        assert "Channels:" in result_status.output
        assert "Posts:" in result_status.output
        assert "Contacts:" in result_status.output
        assert "Tags:" in result_status.output
        assert "testchannel" in result_status.output
        assert "Test Channel" in result_status.output

        # --- Step 6: Verify DB data matches status output ---
        conn = get_connection(db_path)
        try:
            ch_count = conn.execute(
                "SELECT COUNT(*) FROM channels"
            ).fetchone()[0]
            post_count = conn.execute(
                "SELECT COUNT(*) FROM posts"
            ).fetchone()[0]
            contact_count = conn.execute(
                "SELECT COUNT(*) FROM contacts"
            ).fetchone()[0]
            tag_count = conn.execute(
                "SELECT COUNT(*) FROM tags"
            ).fetchone()[0]

            assert ch_count == 1
            assert post_count == 3
            assert contact_count > 0
            assert tag_count > 0

            phones = conn.execute(
                "SELECT value FROM contacts WHERE type = 'phone'"
            ).fetchall()
            assert len(phones) >= 1
            phone_values = {r["value"] for r in phones}
            assert "+996555123456" in phone_values

            locations = conn.execute(
                "SELECT value FROM tags WHERE type = 'location'"
            ).fetchall()
            loc_values = {r["value"] for r in locations}
            assert "Бишкек" in loc_values or "Москва" in loc_values
        finally:
            conn.close()

    def test_status_empty_db(self) -> None:
        """Status on empty DB shows zeros and helpful message."""
        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Channels:  0" in result.output
        assert "Posts:     0" in result.output
        assert "No channels" in result.output

    def test_status_with_data(self) -> None:
        """Status shows correct counts after data is inserted."""
        db_path = Path(os.environ["TH_DB"])
        conn = get_connection(db_path)
        try:
            conn.execute(
                "INSERT INTO channels (telegram_id, name) "
                "VALUES (?, ?)",
                ("ch1", "Channel One"),
            )
            conn.execute(
                "INSERT INTO channels (telegram_id, name) "
                "VALUES (?, ?)",
                ("ch2", "Channel Two"),
            )
            conn.execute(
                "INSERT INTO posts "
                "(channel_id, telegram_post_id, raw_text) "
                "VALUES (1, '100', 'Post 1')"
            )
            conn.execute(
                "INSERT INTO posts "
                "(channel_id, telegram_post_id, raw_text) "
                "VALUES (1, '101', 'Post 2')"
            )
            conn.execute(
                "INSERT INTO posts "
                "(channel_id, telegram_post_id, raw_text) "
                "VALUES (2, '200', 'Post 3')"
            )
            conn.execute(
                "INSERT INTO contacts "
                "(post_id, type, value) "
                "VALUES (1, 'phone', '+996555123456')"
            )
            conn.execute(
                "INSERT INTO tags (post_id, type, value) "
                "VALUES (1, 'location', 'Бишкек')"
            )
            conn.commit()
        finally:
            conn.close()

        result = runner.invoke(app, ["status"])
        assert result.exit_code == 0
        assert "Channels:  2" in result.output
        assert "Posts:     3" in result.output
        assert "Contacts:  1" in result.output
        assert "Tags:      1" in result.output
        assert "ch1" in result.output
        assert "ch2" in result.output
        assert "Channel One" in result.output
