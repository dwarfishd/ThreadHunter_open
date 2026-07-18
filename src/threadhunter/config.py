"""Configuration loading and validation for ThreadHunter."""

import logging
import os
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import BaseModel, ValidationError, field_validator

logger = logging.getLogger(__name__)

# Package-level reference to the loaded settings; None until load_config() is called.
_settings: Optional["Settings"] = None


class Settings(BaseModel):
    """Validated configuration from .env file."""

    api_id: Optional[int] = None
    api_hash: Optional[str] = None
    session_name: str = "threadhunter"

    @field_validator("api_id", mode="before")
    @classmethod
    def validate_api_id(cls, v: object) -> Optional[int]:
        if v is None or v == "":
            return None
        try:
            return int(v)  # type: ignore[call-overload,no-any-return]
        except (ValueError, TypeError):
            raise ValueError(f"API_ID must be an integer, got: {v!r}")

    @field_validator("api_hash", mode="before")
    @classmethod
    def validate_api_hash(cls, v: object) -> Optional[str]:
        if v is None or v == "":
            return None
        s = str(v).strip()
        if not s:
            return None
        return s

    @property
    def has_telegram_credentials(self) -> bool:
        """Return True if both API_ID and API_HASH are present and valid."""
        return self.api_id is not None and self.api_hash is not None


def _find_env_file() -> Optional[Path]:
    """Look for .env in the current working directory."""
    candidate = Path.cwd() / ".env"
    if candidate.is_file():
        return candidate
    return None


def load_config() -> Settings:
    """Load and validate .env configuration.

    Returns a validated Settings object. Warns (via logger) if API_ID or
    API_HASH are missing, but does not raise — callers should check
    ``settings.has_telegram_credentials`` for fail-fast behaviour.
    """
    global _settings

    env_file = _find_env_file()
    if env_file:
        load_dotenv(env_file, override=True)
        logger.info("Loaded configuration from %s", env_file)
    else:
        logger.info("No .env file found; using environment variables / defaults")

    # Re-read from os.environ (dotenv sets them there)
    raw_api_id = os.environ.get("API_ID")
    raw_api_hash = os.environ.get("API_HASH")
    raw_session = os.environ.get("SESSION_NAME")

    try:
        kwargs: dict[str, object] = {}
        if raw_api_id is not None:
            kwargs["api_id"] = raw_api_id
        if raw_api_hash is not None:
            kwargs["api_hash"] = raw_api_hash
        if raw_session is not None:
            kwargs["session_name"] = raw_session

        _settings = Settings(**kwargs)  # type: ignore[arg-type]
    except ValidationError as exc:
        errors = ", ".join(
            str(err["loc"][0]) for err in exc.errors() if err.get("loc")
        )
        logger.error("Invalid configuration for: %s", errors)
        raise

    # Warnings for missing credentials
    if _settings.api_id is None:
        logger.warning(
            "API_ID is not set. "
            "Run 'th init' and edit .env with your Telegram API credentials."
        )
    if _settings.api_hash is None:
        logger.warning(
            "API_HASH is not set. "
            "Run 'th init' and edit .env with your Telegram API credentials."
        )

    return _settings


def get_settings() -> Settings:
    """Return the currently loaded settings, or load them if not yet loaded."""
    if _settings is None:
        return load_config()
    return _settings


def reset_settings() -> None:
    """Reset the global settings cache. Useful for testing."""
    global _settings
    _settings = None
