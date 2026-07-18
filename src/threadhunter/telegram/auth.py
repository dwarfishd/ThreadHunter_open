"""Telethon authorization flow for ThreadHunter."""

import logging
import os
import time
from pathlib import Path
from typing import Optional

from telethon import TelegramClient

logger = logging.getLogger(__name__)

SESSION_DIR = Path.home() / ".threadhunter"
SESSION_EXT = ".session"

# Cache for session validity check (avoids repeated TCP connections)
_session_cache: dict[str, tuple[bool, float]] = {}
_SESSION_CACHE_TTL = 300  # 5 minutes


def get_session_path(session_name: Optional[str] = None) -> Path:
    """Return the path to the Telethon .session file.

    Resolution order:
    1. TH_SESSION environment variable (full path)
    2. ~/.threadhunter/{session_name}.session  (session_name from Settings)
    3. ~/.threadhunter/threadhunter.session   (default)
    """
    env_path = os.environ.get("TH_SESSION")
    if env_path:
        return Path(env_path)

    if session_name is None:
        # Use cached settings to avoid repeated .env parsing
        from threadhunter.config import get_settings

        settings = get_settings()
        session_name = settings.session_name

    return SESSION_DIR / f"{session_name}{SESSION_EXT}"


async def start_auth(
    phone: str,
    session_path: Path,
    code: str,
    api_id: int,
    api_hash: str,
) -> Path:
    """Run the Telethon authorization flow.

    Creates a TelegramClient, sends the code request, signs in, and
    saves the session file.

    Args:
        phone: Phone number in international format (e.g. +996555123456).
        session_path: Where to store the .session file.
        code: Verification code received via Telegram.
        api_id: Telegram API application ID.
        api_hash: Telegram API application hash.

    Returns:
        The path to the saved session file.

    Raises:
        CodeInvalidError: If the code is wrong or expired.
        SessionPasswordNeededError: If 2FA password is required.
        FloodWaitError: If rate-limited (includes .seconds attribute).
    """
    session_path.parent.mkdir(parents=True, exist_ok=True)

    client = TelegramClient(
        str(session_path.with_suffix("")),
        api_id,
        api_hash,
    )

    try:
        await client.connect()
        if not await client.is_user_authorized():
            await client.send_code_request(phone)
            await client.sign_in(phone, code)
        # Persist session to disk
        await client.session.save()
    finally:
        await client.disconnect()

    # Invalidate cache after successful auth
    invalidate_session_cache(session_path)

    return session_path


async def check_session(session_path: Path) -> bool:
    """Check whether a session file exists and is valid.

    Uses a 5-minute cache to avoid repeated TCP connections to Telegram API.

    Args:
        session_path: Path to the .session file (without extension for Telethon).

    Returns:
        True if the session file exists and the client can connect
        and is authorized.
    """
    if not session_path.exists():
        return False

    # Check cache first
    cache_key = str(session_path)
    now = time.time()
    if cache_key in _session_cache:
        cached_valid, cached_time = _session_cache[cache_key]
        if now - cached_time < _SESSION_CACHE_TTL:
            logger.debug("Session check: cache hit (valid=%s)", cached_valid)
            return cached_valid

    # Cache miss or expired — check for real
    stem = session_path.with_suffix("")

    from threadhunter.config import get_settings

    settings = get_settings()
    if not settings.has_telegram_credentials:
        logger.warning("No valid API credentials to verify session")
        return False

    client = TelegramClient(
        str(stem),
        settings.api_id,
        settings.api_hash,
    )

    try:
        await client.connect()
        is_valid = bool(await client.is_user_authorized())
        # Update cache
        _session_cache[cache_key] = (is_valid, now)
        return is_valid
    except Exception:
        logger.exception("Session validation failed")
        _session_cache[cache_key] = (False, now)
        return False
    finally:
        await client.disconnect()


def invalidate_session_cache(session_path: Optional[Path] = None) -> None:
    """Invalidate session cache for a specific path or all paths.

    Call this after start_auth() to ensure next check_session() re-validates.
    """
    if session_path is None:
        _session_cache.clear()
    else:
        cache_key = str(session_path)
        _session_cache.pop(cache_key, None)
