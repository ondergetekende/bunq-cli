"""Accounts commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "description", "type", "currency", "balance", "iban", "status"]


@click.group()
def accounts() -> None:
    """Manage monetary accounts."""


@accounts.command("list")
@click.option("--include-inactive", is_flag=True, help="Include closed accounts.")
@pass_context
def list_accounts(ctx: Context, include_inactive: bool) -> None:
    """List all monetary accounts."""
    client = ctx.get_client()
    data = client.list_accounts()
    if not include_inactive:
        data = [a for a in data if a.get("status") == "ACTIVE"]
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@accounts.command("get")
@click.argument("id", type=int)
@pass_context
def get_account(ctx: Context, id: int) -> None:
    """Get a single monetary account by ID."""
    client = ctx.get_client()
    data = client.get_account(id)
    echo_output(data, fmt=ctx.output_format)
