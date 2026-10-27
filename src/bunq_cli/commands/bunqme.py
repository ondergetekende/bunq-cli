"""bunq.me payment link commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "created", "status", "amount", "currency", "description", "url"]


@click.group()
def bunqme() -> None:
    """Manage bunq.me payment links."""


@bunqme.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def list_tabs(ctx: Context, account_id: int | None) -> None:
    """List bunq.me payment links."""
    client = ctx.get_client()
    data = client.list_bunqme_tabs(account_id=account_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@bunqme.command("get")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def get_tab(ctx: Context, id: int, account_id: int | None) -> None:
    """Get a single bunq.me payment link."""
    client = ctx.get_client()
    data = client.get_bunqme_tab(id, account_id=account_id)
    echo_output(data, fmt=ctx.output_format)


@bunqme.command("create")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--amount", required=True, help="Amount to request (e.g., 15.00).")
@click.option("--currency", default="EUR", help="Currency code (default: EUR).")
@click.option("--description", required=True, help="Description shown to the payer.")
@click.option("--redirect-url", default=None, help="URL to send the payer to after paying.")
@pass_context
def create_tab(
    ctx: Context,
    account_id: int | None,
    amount: str,
    currency: str,
    description: str,
    redirect_url: str | None,
) -> None:
    """Create a bunq.me payment link."""
    client = ctx.get_client()
    data = client.create_bunqme_tab(
        amount=amount,
        currency=currency,
        description=description,
        redirect_url=redirect_url,
        account_id=account_id,
    )
    echo_output(data, fmt=ctx.output_format)


@bunqme.command("cancel")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def cancel_tab(ctx: Context, id: int, account_id: int | None) -> None:
    """Cancel a bunq.me payment link."""
    client = ctx.get_client()
    client.cancel_bunqme_tab(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"bunq.me link {id} cancelled.")
