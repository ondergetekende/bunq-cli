"""Callbacks (notification filter) commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "category", "notification_target"]

CATEGORIES = [
    "MUTATION",
    "PAYMENT",
    "INSTANT_PAYMENT",
    "PAYMENT_DELAYED",
    "PAYMENT_SUSPENDED",
    "PAYMENT_UPDATED",
    "DRAFT_PAYMENT",
    "REQUEST",
    "SCHEDULE_RESULT",
    "SCHEDULE_STATUS",
    "IDEAL",
    "SOFORT",
    "CARD_TRANSACTION_SUCCESSFUL",
    "CARD_TRANSACTION_FAILED",
    "CARD_TRANSACTION_UPDATED",
    "CARD_TRANSACTION_REFUND",
    "CARD_TRANSACTION_TOKENIZED",
    "CARD_DYNAMIC_CURRENCY_CONVERSION_WARNING",
    "CARD_EXPIRY",
    "CARD_REPLACEMENT",
    "CARD_COUNTRY_PERMISSION",
    "CARD_TOKENIZATION",
    "MASTERCARD_IDENTITY_CHECK",
    "MONETARY_ACCOUNT_BALANCE",
    "MONETARY_ACCOUNT_JOINT",
    "CO_OWNER_INVITE",
    "APPROVAL_REQUEST_USER",
    "APPROVAL_REQUEST_MONETARY_ACCOUNT",
    "WHITELIST",
    "WHITELIST_RESULT",
    "TAB_RESULT",
    "BUNQME_TAB",
    "BUNQME_TAB_RESULT_INQUIRY",
    "BUNQME_TAB_RESULT_RESPONSE",
    "OAUTH",
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
    if not url.lower().startswith("https://"):
        raise click.BadParameter("bunq requires an HTTPS callback URL.", param_hint="--url")
    client = ctx.get_client()
    data = client.create_callback(url, [c.upper() for c in categories])
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
