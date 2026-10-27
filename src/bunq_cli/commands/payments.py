"""Payments commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context, yes_option
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "created", "amount", "currency", "counterparty", "description"]


@click.group()
def payments() -> None:
    """Manage payments."""


@payments.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--all", "fetch_all", is_flag=True, help="Fetch all pages.")
@click.option("--count", type=int, default=25, help="Number of results per page.")
@click.option("--older-id", type=int, default=None, help="Cursor: fetch results older than this ID.")
@click.option("--newer-id", type=int, default=None, help="Cursor: fetch results newer than this ID.")
@pass_context
def list_payments(
    ctx: Context,
    account_id: int | None,
    fetch_all: bool,
    count: int,
    older_id: int | None,
    newer_id: int | None,
) -> None:
    """List payments. Returns one page by default; use --all to fetch everything."""
    client = ctx.get_client()
    if fetch_all:
        data = client.list_all_payments(account_id=account_id)
    else:
        data = client.list_payments(
            account_id=account_id,
            count=count,
            older_id=older_id,
            newer_id=newer_id,
        )
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@payments.command("get")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@pass_context
def get_payment(ctx: Context, id: int, account_id: int | None) -> None:
    """Get a single payment by ID."""
    client = ctx.get_client()
    data = client.get_payment(id, account_id=account_id)
    echo_output(data, fmt=ctx.output_format)


@payments.command("create")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--amount", required=True, help="Amount to send (e.g., 25.00).")
@click.option("--currency", default="EUR", help="Currency code (default: EUR).")
@click.option("--recipient-iban", required=True, help="Recipient IBAN.")
@click.option("--recipient-name", required=True, help="Recipient name.")
@click.option("--description", required=True, help="Payment description.")
@yes_option
@pass_context
def create_payment(
    ctx: Context,
    account_id: int | None,
    amount: str,
    currency: str,
    recipient_iban: str,
    recipient_name: str,
    description: str,
    yes: bool,
) -> None:
    """Create a payment."""
    client = ctx.get_client(write=True)
    source = f"account {account_id}" if account_id else "the primary account"
    ctx.confirm(f"Pay {amount} {currency} to {recipient_name} ({recipient_iban}) from {source}?", yes)
    payment_id = client.create_payment(
        amount=amount,
        currency=currency,
        recipient_iban=recipient_iban,
        recipient_name=recipient_name,
        description=description,
        account_id=account_id,
    )
    if not ctx.quiet:
        click.echo(f"Payment created (ID: {payment_id}).")
