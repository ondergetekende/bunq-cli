"""Event (activity feed) commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "created", "action", "object_type", "object_id", "account_id", "status"]


@click.group()
def events() -> None:
    """View the account activity feed."""


@events.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Only events for this monetary account.")
@click.option("--count", type=int, default=25, help="Number of results.")
@click.option("--older-id", type=int, default=None, help="Cursor: fetch results older than this ID.")
@pass_context
def list_events(ctx: Context, account_id: int | None, count: int, older_id: int | None) -> None:
    """List recent events."""
    client = ctx.get_client()
    data = client.list_events(account_id=account_id, count=count, older_id=older_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@events.command("get")
@click.argument("id", type=int)
@pass_context
def get_event(ctx: Context, id: int) -> None:
    """Get a single event, including the object it refers to."""
    client = ctx.get_client()
    data = client.get_event(id)
    echo_output(data, fmt=ctx.output_format)
