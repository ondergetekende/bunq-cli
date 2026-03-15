"""Bunq CLI - main entry point and global options."""

from __future__ import annotations

from pathlib import Path

import click

from bunq_cli.client import BunqClient
from bunq_cli.config import (
    DEFAULT_CONFIG_PATH,
    DEFAULT_CONTEXT_PATH,
    get_credentials,
    load_config,
)


class Context:
    """Shared context for all commands."""

    def __init__(self) -> None:
        self.verbose: bool = False
        self.quiet: bool = False
        self.output_format: str = "auto"
        self.no_color: bool = False
        self.sandbox: bool = False
        self.config_path: Path = DEFAULT_CONFIG_PATH
        self.token: str | None = None

    def get_client(self) -> BunqClient:
        """Build a BunqClient from config/options."""
        config = load_config(self.config_path)
        creds = get_credentials(config)

        context_path = creds.get("context_path", str(DEFAULT_CONTEXT_PATH))
        sandbox = self.sandbox or creds.get("sandbox", False)

        return BunqClient(
            context_path=Path(context_path),
            sandbox=sandbox,
            verbose=self.verbose,
        )


pass_context = click.make_pass_decorator(Context, ensure=True)


@click.group()
@click.version_option(version="0.1.0", prog_name="bunq")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output except errors.")
@click.option("--token", metavar="TOKEN", help="API token (overrides stored credentials).")
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["auto", "json", "table"]),
    default="auto",
    help="Output format.",
)
@click.option("--no-color", is_flag=True, help="Disable colored output.")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Custom config file path.",
)
@click.option("--sandbox", is_flag=True, help="Use the sandbox environment.")
@pass_context
def cli(
    ctx: Context,
    verbose: bool,
    quiet: bool,
    token: str | None,
    output_format: str,
    no_color: bool,
    config_path: Path | None,
    sandbox: bool,
) -> None:
    """Bunq CLI - interact with the Bunq API from your terminal."""
    ctx.verbose = verbose
    ctx.quiet = quiet
    ctx.output_format = output_format
    ctx.no_color = no_color
    ctx.sandbox = sandbox
    ctx.token = token
    if config_path:
        ctx.config_path = config_path


# Register commands
from bunq_cli.commands.login import login, logout  # noqa: E402
from bunq_cli.commands.accounts import accounts  # noqa: E402
from bunq_cli.commands.payments import payments  # noqa: E402
from bunq_cli.commands.requests import requests  # noqa: E402
from bunq_cli.commands.cards import cards  # noqa: E402
from bunq_cli.commands.callbacks import callbacks  # noqa: E402

cli.add_command(login)
cli.add_command(logout)
cli.add_command(accounts)
cli.add_command(payments)
cli.add_command(requests)
cli.add_command(cards)
cli.add_command(callbacks)
