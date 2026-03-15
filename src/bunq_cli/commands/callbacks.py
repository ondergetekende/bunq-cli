"""Callbacks (notification filter) commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "category", "notification_target"]

CATEGORIES = [
    "BILLING",
    "CARD_TRANSACTION_SUCCESSFUL",
    "CARD_TRANSACTION_FAILED",
    "CHAT",
    "DRAFT_PAYMENT",
    "IDEAL",
    "SOFORT",
    "MUTATION",
    "PAYMENT",
    "REQUEST",
    "SCHEDULE_RESULT",
    "SCHEDULE_STATUS",
    "SHARE",
    "TAB_RESULT",
    "BUNQME_TAB",
    "SUPPORT",
]


@click.group()
def callbacks() -> None:
    """Manage notification filters (webhooks)."""


@callbacks.command("list")
@pass_context
def list_callbacks(ctx: Context) -> None:
    """List all notification filters."""
    client = ctx.get_client()
    data = client.list_callbacks()
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@callbacks.command("create")
@click.option("--url", required=True, help="Callback URL.")
@click.option(
    "--category",
    "categories",
    multiple=True,
    type=click.Choice(CATEGORIES, case_sensitive=False),
    required=True,
    help="Event category (can be specified multiple times).",
)
@pass_context
def create_callback(ctx: Context, url: str, categories: tuple[str, ...]) -> None:
    """Create notification filters for one or more event categories."""
    client = ctx.get_client()
    data = client.create_callback(url, list(categories))
    if not ctx.quiet:
        click.echo(f"Created {len(categories)} notification filter(s).")
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@callbacks.command("delete")
@click.confirmation_option(prompt="This will remove ALL notification filters. Continue?")
@pass_context
def delete_callbacks(ctx: Context) -> None:
    """Remove all notification filters."""
    client = ctx.get_client()
    client.delete_all_callbacks()
    if not ctx.quiet:
        click.echo("All notification filters removed.")
