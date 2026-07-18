"""Logging configuration for ThreadHunter.

INFO and above → stderr
DEBUG and above → ~/.threadhunter/threadhunter.log
"""

import logging
import sys
from pathlib import Path

_LOG_DIR = Path.home() / ".threadhunter"
_LOG_FILE = _LOG_DIR / "threadhunter.log"


def setup_logging() -> None:
    """Configure root logger with stderr (INFO) and file (DEBUG) handlers."""
    if _LOG_DIR.exists() and not _LOG_DIR.is_dir():
        raise ValueError(
            f"Log directory exists but is not a directory: {_LOG_DIR}"
        )
    _LOG_DIR.mkdir(parents=True, exist_ok=True)

    root_logger = logging.getLogger("threadhunter")
    root_logger.setLevel(logging.DEBUG)

    # Clear any existing handlers to avoid duplicates on re-init
    root_logger.handlers.clear()

    # File handler: DEBUG and above
    file_handler = logging.FileHandler(_LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    root_logger.addHandler(file_handler)

    # Stderr handler: INFO and above
    stderr_handler = logging.StreamHandler(sys.stderr)
    stderr_handler.setLevel(logging.INFO)
    stderr_fmt = logging.Formatter("[%(levelname)s] %(message)s")
    stderr_handler.setFormatter(stderr_fmt)
    root_logger.addHandler(stderr_handler)
