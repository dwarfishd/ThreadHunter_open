"""Shared test fixtures for ThreadHunter."""

import pytest


@pytest.fixture
def cli_runner():
    """Return a CliRunner instance for testing Typer commands."""
    from typer.testing import CliRunner

    return CliRunner()
