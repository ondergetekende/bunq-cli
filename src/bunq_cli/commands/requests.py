"""Payment request commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context, yes_option
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "created", "amount", "currency", "counterparty", "description", "status"]


@click.group()
def requests() -> None:
    """Manage payment requests."""


@requests.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@pass_context
def list_requests(ctx: Context, account_id: int | None) -> None:
    """List outgoing payment requests."""
    client = ctx.get_client()
    data = client.list_requests(account_id=account_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@requests.command("get")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@pass_context
def get_request(ctx: Context, id: int, account_id: int | None) -> None:
    """Get a single outgoing payment request."""
    client = ctx.get_client()
    data = client.get_request(id, account_id=account_id)
    echo_output(data, fmt=ctx.output_format)


@requests.command("create")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@click.option("--amount", required=True, help="Amount to request (e.g., 35.00).")
@click.option("--currency", default="EUR", help="Currency code (default: EUR).")
@click.option("--counterparty-email", default=None, help="Recipient email address.")
@click.option("--counterparty-phone", default=None, help="Recipient phone number (e.g., +31612345678).")
@click.option("--description", required=True, help="Request description.")
@pass_context
def create_request(
    ctx: Context,
    account_id: int | None,
    amount: str,
    currency: str,
    counterparty_email: str | None,
    counterparty_phone: str | None,
    description: str,
) -> None:
    """Create a payment request."""
    if counterparty_email:
        cp_type, cp_value = "EMAIL", counterparty_email
    elif counterparty_phone:
        cp_type, cp_value = "PHONE_NUMBER", counterparty_phone
    else:
        raise click.ClickException("Provide --counterparty-email or --counterparty-phone.")

    client = ctx.get_client(write=True)
    request_id = client.create_request(
        amount=amount,
        currency=currency,
        counterparty_type=cp_type,
        counterparty_value=cp_value,
        description=description,
        account_id=account_id,
    )
    if not ctx.quiet:
        click.echo(f"Payment request created (ID: {request_id}).")


@requests.command("revoke")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@pass_context
def revoke_request(ctx: Context, id: int, account_id: int | None) -> None:
    """Revoke a pending payment request."""
    client = ctx.get_client(write=True)
    client.revoke_request(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"Request {id} revoked.")


@requests.command("incoming")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@pass_context
def list_incoming(ctx: Context, account_id: int | None) -> None:
    """List incoming payment requests."""
    client = ctx.get_client()
    data = client.list_incoming_requests(account_id=account_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@requests.command("accept")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@yes_option
@pass_context
def accept_request(ctx: Context, id: int, account_id: int | None, yes: bool) -> None:
    """Accept (and pay) an incoming payment request."""
    client = ctx.get_client(write=True)
    ctx.confirm(f"Accept and pay incoming request {id}?", yes)
    client.accept_request(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"Request {id} accepted.")


@requests.command("reject")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID.")
@pass_context
def reject_request(ctx: Context, id: int, account_id: int | None) -> None:
    """Reject an incoming payment request."""
    client = ctx.get_client(write=True)
    client.reject_request(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"Request {id} rejected.")
