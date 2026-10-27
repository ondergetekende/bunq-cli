"""Draft payment commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "created", "status", "amount", "currency", "counterparty", "description"]


@click.group("draft-payments")
def drafts() -> None:
    """Manage draft payments (approved in the bunq app)."""


@drafts.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def list_drafts(ctx: Context, account_id: int | None) -> None:
    """List draft payments."""
    client = ctx.get_client()
    data = client.list_draft_payments(account_id=account_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@drafts.command("get")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def get_draft(ctx: Context, id: int, account_id: int | None) -> None:
    """Get a single draft payment."""
    client = ctx.get_client()
    data = client.get_draft_payment(id, account_id=account_id)
    echo_output(data, fmt=ctx.output_format)


@drafts.command("create")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--amount", required=True, help="Amount to send (e.g., 25.00).")
@click.option("--currency", default="EUR", help="Currency code (default: EUR).")
@click.option("--recipient-iban", required=True, help="Recipient IBAN.")
@click.option("--recipient-name", required=True, help="Recipient name.")
@click.option("--description", required=True, help="Payment description.")
@pass_context
def create_draft(
    ctx: Context,
    account_id: int | None,
    amount: str,
    currency: str,
    recipient_iban: str,
    recipient_name: str,
    description: str,
) -> None:
    """Create a draft payment. It is only executed after approval in the bunq app."""
    client = ctx.get_client(write=True)
    draft_id = client.create_draft_payment(
        amount=amount,
        currency=currency,
        recipient_iban=recipient_iban,
        recipient_name=recipient_name,
        description=description,
        account_id=account_id,
    )
    if not ctx.quiet:
        click.echo(f"Draft payment created (ID: {draft_id}). Approve it in the bunq app.")


@drafts.command("reject")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def reject_draft(ctx: Context, id: int, account_id: int | None) -> None:
    """Reject (withdraw) a pending draft payment."""
    client = ctx.get_client(write=True)
    client.reject_draft_payment(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"Draft payment {id} rejected.")
