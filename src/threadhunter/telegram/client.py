"""Async Telethon client wrapper for ThreadHunter."""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from telethon import TelegramClient
from telethon.errors import (
    ChannelInvalidError,
    ChannelPrivateError,
    FloodWaitError,
)
from telethon.tl.types import Message

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_BASE_BACKOFF = 1.0


class TelegramClientWrapper:
    """Async context-manager wrapper around TelegramClient.

    Provides ``get_entity``, ``get_messages``, ``connect``, ``disconnect``
    with retry / backoff for transient API errors.
    """

    def __init__(
        self,
        session_path: Path,
        api_id: int,
        api_hash: str,
    ) -> None:
        self._session_path = session_path
        self._api_id = api_id
        self._api_hash = api_hash
        self._client: Optional[TelegramClient] = None

    async def __aenter__(self) -> "TelegramClientWrapper":
        await self.connect()
        return self

    async def __aexit__(self, *exc: object) -> None:
        await self.disconnect()

    @property
    def client(self) -> TelegramClient:
        """Return the underlying TelegramClient, raising if not connected."""
        if self._client is None:
            raise RuntimeError("Client is not connected. Call connect() first.")
        return self._client

    async def connect(self) -> None:
        """Create and connect the TelegramClient."""
        stem = self._session_path.with_suffix("")
        self._client = TelegramClient(str(stem), self._api_id, self._api_hash)
        await self._client.connect()

    async def disconnect(self) -> None:
        """Close the Telegram connection."""
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def get_entity(self, channel: str) -> Any:
        """Resolve a channel username / invite link to an entity.

        Retries on FloodWaitError.  Raises ChannelPrivateError /
        ChannelInvalidError unchanged so callers can handle them.
        """
        return await self._with_retry(self.client.get_entity, channel)

    async def get_messages(
        self,
        entity: Any,
        limit: int = 100,
        offset_date: Optional[datetime] = None,
        offset_id: int = 0,
    ) -> list[Message]:
        """Fetch messages from *entity* with pagination support.

        Returns a list of Message objects (newest first).
        Retries on FloodWaitError and network timeouts.

        Pass both ``offset_date`` and ``offset_id`` for correct pagination
        when multiple messages share the same timestamp.
        """

        async def _fetch() -> Any:
            kwargs: dict[str, Any] = {"limit": limit}
            if offset_date is not None:
                kwargs["offset_date"] = offset_date
            if offset_id:
                kwargs["offset_id"] = offset_id
            return await self.client.get_messages(entity, **kwargs)

        return await self._with_retry(_fetch)  # type: ignore[no-any-return]

    async def _with_retry(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute *func* with retry on FloodWaitError / OSError."""
        backoff = _BASE_BACKOFF
        last_exc: Optional[Exception] = None
        for attempt in range(_MAX_RETRIES):
            try:
                result = func(*args, **kwargs)
                if asyncio.iscoroutine(result):
                    result = await result
                return result
            except FloodWaitError as exc:
                logger.warning(
                    "FloodWait: sleeping %ds (attempt %d/%d)",
                    exc.seconds,
                    attempt + 1,
                    _MAX_RETRIES,
                )
                await asyncio.sleep(exc.seconds)
                last_exc = exc
            except (ChannelPrivateError, ChannelInvalidError):
                raise
            except OSError as exc:
                logger.warning(
                    "Network error: %s (attempt %d/%d, backoff %.1fs)",
                    exc,
                    attempt + 1,
                    _MAX_RETRIES,
                    backoff,
                )
                last_exc = exc
                if attempt < _MAX_RETRIES - 1:
                    await asyncio.sleep(backoff)
                    backoff *= 3
        raise last_exc  # type: ignore[misc]
