"""ThreadHunter CLI entry point."""

import asyncio
import logging
import os
import shutil
import stat
from datetime import datetime
from pathlib import Path
from typing import Optional

import typer
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    CodeInvalidError,
    FloodWaitError,
    SessionPasswordNeededError,
)

from threadhunter.channels import add_channel as db_add_channel
from threadhunter.channels import list_channels, update_last_parsed
from threadhunter.config import load_config
from threadhunter.db import Channel, get_db_path, init_db
from threadhunter.logging_config import setup_logging
from threadhunter.pipeline import process_channel
from threadhunter.posts import insert_post
from threadhunter.telegram.auth import check_session, get_session_path, start_auth
from threadhunter.telegram.client import TelegramClientWrapper

app = typer.Typer(
    name="th",
    help="ThreadHunter — parse Telegram channels for garment manufacturing ads.",
    add_completion=False,
)

logger = logging.getLogger(__name__)


@app.command()
def init() -> None:
    """Initialize project: create database and config."""
    setup_logging()

    # Create .env from template if it doesn't exist
    env_file = Path.cwd() / ".env"
    env_example = Path.cwd() / ".env.example"
    if not env_file.exists() and env_example.exists():
        shutil.copy2(env_example, env_file)
        # Restrict to owner-only read/write (0600)
        os.chmod(env_file, stat.S_IRUSR | stat.S_IWUSR)
        logger.info("Created .env from template")
    elif env_file.exists():
        logger.info(".env already exists — not overwriting")
    else:
        logger.warning("No .env.example template found; skipping .env creation")

    # Create database with schema
    init_db()
    logger.info("Database initialized at %s", init_db.__module__)

    typer.echo("ThreadHunter initialized successfully.")
    typer.echo(f"  Database: {get_db_path()}")
    if env_file.exists():
        typer.echo(f"  Config: {env_file}")
    typer.echo("Edit .env with your Telegram API credentials, then run 'th auth'.")


@app.command("add-channel")
def add_channel(channel: str) -> None:
    """Add a Telegram channel to watch."""
    setup_logging()

    if not channel.strip():
        raise typer.BadParameter("channel name cannot be empty")

    settings = load_config()
    if not settings.has_telegram_credentials:
        typer.echo(
            "Error: API_ID and API_HASH are required. "
            "Run 'th init' and edit .env with your Telegram API credentials.",
            err=True,
        )
        raise typer.Exit(code=1)

    session_path = get_session_path(settings.session_name)
    if not session_path.exists():
        typer.echo(
            "Error: Session not found. Run 'th auth' to authorize.",
            err=True,
        )
        raise typer.Exit(code=1)

    try:
        asyncio.run(_add_channel_async(channel, session_path, settings))
    except (ChannelPrivateError, ChannelInvalidError):
        typer.echo(
            f"Error: Channel '{channel}' is private or does not exist.",
            err=True,
        )
        raise typer.Exit(code=1)
    except FloodWaitError as exc:
        typer.echo(
            f"Error: Rate-limited. Please wait {exc.seconds} seconds.",
            err=True,
        )
        raise typer.Exit(code=1)
    except Exception as exc:
        logger.error("Failed to add channel '%s': %s", channel, exc)
        typer.echo(
            f"Error: Could not resolve channel '{channel}'. "
            "Check the name and try again.",
            err=True,
        )
        raise typer.Exit(code=1)


async def _add_channel_async(
    channel: str, session_path: Path, settings: object
) -> None:
    """Resolve channel via Telegram API and save to database."""
    from threadhunter.config import Settings

    s = settings if isinstance(settings, Settings) else load_config()
    async with TelegramClientWrapper(
        session_path=session_path,
        api_id=s.api_id,  # type: ignore[arg-type]
        api_hash=s.api_hash,  # type: ignore[arg-type]
    ) as client:
        entity = await client.get_entity(channel)
        name = getattr(entity, "title", None) or channel
        telegram_id = channel.lstrip("@") if channel.startswith("@") else channel
        db_add_channel(telegram_id=telegram_id, name=name)
        typer.echo(f"Channel '{name}' ({telegram_id}) added.")


@app.command()
def auth() -> None:
    """Authorize with Telegram API (phone → code → session)."""
    setup_logging()
    settings = load_config()

    if not settings.has_telegram_credentials:
        typer.echo(
            "Error: API_ID and API_HASH are required. "
            "Run 'th init' and edit .env with your Telegram API credentials.",
            err=True,
        )
        raise typer.Exit(code=1)

    session_path = get_session_path(settings.session_name)

    # Check if session is already valid
    if session_path.exists():
        typer.echo(f"Session file found: {session_path}")
        is_valid = asyncio.run(check_session(session_path))
        if is_valid:
            typer.echo("Session is valid. No need to re-authorize.")
            confirm = typer.confirm("Re-authorize anyway?")
            if not confirm:
                return
        else:
            typer.echo("Session file exists but is invalid. Re-authorizing...")

    phone = typer.prompt("Phone number (international format, e.g. +996555123456)")
    code = typer.prompt("Verification code from Telegram")

    max_retries = 2
    backoff_seconds = 3

    for attempt in range(1, max_retries + 1):
        try:
            typer.echo("Authorizing...")
            asyncio.run(
                start_auth(
                    phone=phone,
                    session_path=session_path,
                    code=code,
                    api_id=settings.api_id,  # type: ignore[arg-type]
                    api_hash=settings.api_hash,  # type: ignore[arg-type]
                )
            )
            typer.echo(f"Authorization successful. Session saved: {session_path}")
            return
        except CodeInvalidError:
            typer.echo(
                "Error: Invalid or expired code. Please try again.",
                err=True,
            )
            code = typer.prompt("Enter a new verification code")
        except SessionPasswordNeededError:
            typer.echo(
                "Error: 2FA password required. "
                "Run 'th auth' again and provide your 2FA password.",
                err=True,
            )
            raise typer.Exit(code=1)
        except FloodWaitError as exc:
            typer.echo(
                f"Error: Too many attempts. Please wait {exc.seconds} seconds.",
                err=True,
            )
            raise typer.Exit(code=1)
        except Exception:
            if attempt < max_retries:
                typer.echo(
                    f"Network error. Retrying in {backoff_seconds}s "
                    f"(attempt {attempt}/{max_retries})...",
                    err=True,
                )
                import time

                time.sleep(backoff_seconds)
                backoff_seconds *= 2
            else:
                typer.echo(
                    "Error: Network timeout after multiple attempts. "
                    "Check your connection and try again.",
                    err=True,
                )
                raise typer.Exit(code=1)


@app.command()
def parse() -> None:
    """Parse added channels, download new posts."""
    setup_logging()
    settings = load_config()
    if not settings.has_telegram_credentials:
        missing = []
        if settings.api_id is None:
            missing.append("API_ID")
        if settings.api_hash is None:
            missing.append("API_HASH")
        logger.error(
            "Missing Telegram credentials: %s. Run 'th init' and edit .env.",
            ", ".join(missing),
        )
        raise typer.Exit(code=1)

    # Check session before proceeding
    session_path = get_session_path(settings.session_name)
    if not session_path.exists():
        typer.echo(
            "Error: Session not found. Run 'th auth' to authorize.",
            err=True,
        )
        raise typer.Exit(code=1)

    is_valid = asyncio.run(check_session(session_path))
    if not is_valid:
        typer.echo(
            "Error: Session is invalid. Run 'th auth' to re-authorize.",
            err=True,
        )
        raise typer.Exit(code=1)

    channels = list_channels()
    if not channels:
        typer.echo("No channels to parse. Use 'th add-channel @name' first.")
        return

    try:
        asyncio.run(_parse_channels_async(channels, session_path, settings))
    except Exception as exc:
        logger.error("Parse failed: %s", exc)
        typer.echo("Error: Parse failed. Check logs for details.", err=True)
        raise typer.Exit(code=1)

    # Phase 4: extract contacts + classify tags for each parsed channel
    total_processed = 0
    for ch in channels:
        if ch.id is not None:
            total_processed += process_channel(ch.id)
    if total_processed:
        typer.echo(f"Processed {total_processed} post(s) for contacts and tags.")


async def _parse_channels_async(
    channels: list[Channel],
    session_path: Path,
    settings: object,
) -> None:
    """Iterate channels, fetch new posts, save to DB."""
    from threadhunter.config import Settings

    s = settings if isinstance(settings, Settings) else load_config()
    total_new = 0

    async with TelegramClientWrapper(
        session_path=session_path,
        api_id=s.api_id,  # type: ignore[arg-type]
        api_hash=s.api_hash,  # type: ignore[arg-type]
    ) as client:
        for idx, ch in enumerate(channels):
            if idx > 0:
                await asyncio.sleep(1)

            try:
                new_count = await _parse_single_channel(client, ch)
                total_new += new_count
            except (ChannelPrivateError, ChannelInvalidError):
                logger.warning(
                    "Channel '%s' is private or invalid — skipping.",
                    ch.telegram_id,
                )
                continue
            except Exception as exc:
                logger.warning(
                    "Error parsing channel '%s': %s — skipping.",
                    ch.telegram_id,
                    exc,
                )
                continue

    typer.echo(f"Parsing complete. {total_new} new post(s) saved.")


async def _parse_single_channel(
    client: TelegramClientWrapper,
    channel: Channel,
) -> int:
    """Fetch and store new posts for one channel. Returns count of new posts."""
    ch = channel
    entity = await client.get_entity(ch.telegram_id)

    new_count = 0
    latest_date: Optional[datetime] = None
    # First call: no offset — get the newest messages.
    # Subsequent calls: paginate backward using the oldest message's
    # date + id as the composite cursor.
    offset_date: Optional[datetime] = None
    offset_id: int = 0
    first_call = True

    while True:
        if first_call:
            messages = await client.get_messages(entity, limit=100)
            first_call = False
        else:
            messages = await client.get_messages(
                entity,
                limit=100,
                offset_date=offset_date,
                offset_id=offset_id,
            )
        if not messages:
            break

        stop = False
        for msg in messages:
            if msg.date is None:
                continue
            if ch.last_parsed is not None and msg.date <= ch.last_parsed:
                stop = True
                break

            raw_text = msg.text or msg.message or ""
            has_photo = bool(msg.photo)
            inserted = insert_post(
                channel_id=ch.id,  # type: ignore[arg-type]
                telegram_post_id=str(msg.id),
                raw_text=raw_text if raw_text else None,
                published_at=msg.date,
                has_photo=has_photo,
            )
            if inserted:
                new_count += 1

            if latest_date is None or msg.date > latest_date:
                latest_date = msg.date

        if stop or len(messages) < 100:
            break

        # Paginate backward using both date and id as composite cursor.
        offset_date = messages[-1].date
        offset_id = messages[-1].id

    if latest_date is not None:
        update_last_parsed(ch.id, latest_date)  # type: ignore[arg-type]

    logger.info(
        "Channel '%s': %d new post(s).",
        ch.telegram_id,
        new_count,
    )
    return new_count


@app.command()
def status() -> None:
    """Show database status: channels, posts, contacts, tags."""
    setup_logging()

    from threadhunter.db import get_connection

    conn = get_connection()
    try:
        table_exists = conn.execute(
            "SELECT COUNT(*) AS cnt FROM sqlite_master "
            "WHERE type='table' AND name='channels'"
        ).fetchone()["cnt"]
        if not table_exists:
            typer.echo(
                "Error: Database not initialized. Run 'th init' first.",
                err=True,
            )
            raise typer.Exit(code=1)

        counts = conn.execute(
            "SELECT "
            "(SELECT COUNT(*) FROM channels) AS channels_count, "
            "(SELECT COUNT(*) FROM posts) AS posts_count, "
            "(SELECT COUNT(*) FROM contacts) AS contacts_count, "
            "(SELECT COUNT(*) FROM tags) AS tags_count"
        ).fetchone()
        channels_count = counts["channels_count"]
        posts_count = counts["posts_count"]
        contacts_count = counts["contacts_count"]
        tags_count = counts["tags_count"]

        typer.echo("ThreadHunter Status")
        typer.echo("-" * 40)
        typer.echo(f"  Channels:  {channels_count}")
        typer.echo(f"  Posts:     {posts_count}")
        typer.echo(f"  Contacts:  {contacts_count}")
        typer.echo(f"  Tags:      {tags_count}")
        typer.echo("")

        if channels_count == 0:
            typer.echo("No channels added. Use 'th add-channel @name'.")
            return

        rows = conn.execute(
            "SELECT c.telegram_id, c.name, c.added_at, c.last_parsed, "
            "COUNT(p.id) AS posts_count "
            "FROM channels c "
            "LEFT JOIN posts p ON p.channel_id = c.id "
            "GROUP BY c.id "
            "ORDER BY c.added_at"
        ).fetchall()

        hdr_name = "Channel"
        hdr_telegram = "Telegram ID"
        hdr_posts = "Posts"
        hdr_last = "Last parsed"

        col_name_w = max(
            len(hdr_name),
            max((len(r["name"] or r["telegram_id"]) for r in rows), default=0),
        )
        col_tg_w = max(
            len(hdr_telegram),
            max((len(r["telegram_id"]) for r in rows), default=0),
        )
        col_posts_w = max(
            len(hdr_posts),
            max((len(str(r["posts_count"])) for r in rows), default=0),
        )
        col_last_w = max(len(hdr_last), 19)

        header = (
            f"  {hdr_name:<{col_name_w}}  "
            f"{hdr_telegram:<{col_tg_w}}  "
            f"{hdr_posts:>{col_posts_w}}  "
            f"{hdr_last:<{col_last_w}}"
        )
        typer.echo(header)
        typer.echo("  " + "-" * (len(header) - 2))

        for r in rows:
            name = r["name"] or r["telegram_id"]
            last = r["last_parsed"] or "never"
            line = (
                f"  {name:<{col_name_w}}  "
                f"{r['telegram_id']:<{col_tg_w}}  "
                f"{r['posts_count']:>{col_posts_w}}  "
                f"{last:<{col_last_w}}"
            )
            typer.echo(line)
    finally:
        conn.close()


@app.command()
def export() -> None:
    """Export parsed data to CSV."""
    print("export ok")


if __name__ == "__main__":
    app()
