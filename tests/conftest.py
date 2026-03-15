"""Shared test fixtures."""

from __future__ import annotations

import pytest
from click.testing import CliRunner

from bunq_cli.main import cli


@pytest.fixture
def runner():
    return CliRunner()


@pytest.fixture
def cli_runner(runner, tmp_path):
    """CLI runner with a temporary config file."""
    config_path = tmp_path / "config.toml"

    def invoke(*args, catch_exceptions=False, **kwargs):
        return runner.invoke(
            cli,
            ["--config", str(config_path), *args],
            catch_exceptions=catch_exceptions,
            **kwargs,
        )

    invoke.config_path = config_path
    return invoke
