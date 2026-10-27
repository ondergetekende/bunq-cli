"""Cards commands."""

from __future__ import annotations

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "type", "product_type", "status", "second_line", "expiry_date", "card_limit"]


@click.group()
def cards() -> None:
    """Manage cards."""


@cards.command("list")
@pass_context
def list_cards(ctx: Context) -> None:
    """List all cards."""
    client = ctx.get_client()
    data = client.list_cards()
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@cards.command("get")
@click.argument("id", type=int)
@pass_context
def get_card(ctx: Context, id: int) -> None:
    """Get a single card by ID."""
    client = ctx.get_client()
    data = client.get_card(id)
    echo_output(data, fmt=ctx.output_format)


@cards.command("freeze")
@click.argument("id", type=int)
@pass_context
def freeze_card(ctx: Context, id: int) -> None:
    """Temporarily freeze a card."""
    client = ctx.get_client()
    client.update_card(id, status="DEACTIVATED")
    if not ctx.quiet:
        click.echo(f"Card {id} frozen.")


@cards.command("unfreeze")
@click.argument("id", type=int)
@pass_context
def unfreeze_card(ctx: Context, id: int) -> None:
    """Unfreeze a frozen card."""
    client = ctx.get_client()
    client.update_card(id, status="ACTIVE")
    if not ctx.quiet:
        click.echo(f"Card {id} unfrozen.")


@cards.command("update")
@click.argument("id", type=int)
@click.option("--daily-limit", type=float, default=None, help="Daily spending limit (e.g., 500.00).")
@click.option("--atm-limit", type=float, default=None, help="Daily ATM withdrawal limit (e.g., 250.00).")
@click.option("--country-permission", "countries", multiple=True, help="Country code the card may be used in (repeatable, replaces the current list).")
@click.option("--change-pin", is_flag=True, help="Prompt for a new PIN code.")
@pass_context
def update_card(
    ctx: Context,
    id: int,
    daily_limit: float | None,
    atm_limit: float | None,
    countries: tuple[str, ...],
    change_pin: bool,
) -> None:
    """Update card settings."""
    from bunq.sdk.model.generated.object_ import AmountObject, CardCountryPermissionObject

    kwargs = {}
    if daily_limit is not None:
        kwargs["card_limit"] = AmountObject(f"{daily_limit:.2f}", "EUR")
    if atm_limit is not None:
        kwargs["card_limit_atm"] = AmountObject(f"{atm_limit:.2f}", "EUR")
    if countries:
        kwargs["country_permission"] = [
            CardCountryPermissionObject(country=c.upper()) for c in countries
        ]
    if change_pin:
        kwargs["pin_code"] = click.prompt("New PIN", hide_input=True, confirmation_prompt=True)

    if not kwargs:
        raise click.ClickException(
            "No updates specified. Use --daily-limit, --atm-limit, --country-permission or --change-pin."
        )

    client = ctx.get_client()
    data = client.update_card(id, **kwargs)
    echo_output(data, fmt=ctx.output_format)


TRANSACTION_COLUMNS = ["id", "created", "amount", "currency", "merchant", "card_id", "decision", "status"]


@cards.command("transactions")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--count", type=int, default=25, help="Number of results.")
@click.option("--older-id", type=int, default=None, help="Cursor: fetch results older than this ID.")
@pass_context
def list_transactions(ctx: Context, account_id: int | None, count: int, older_id: int | None) -> None:
    """List card transactions (authorisations, declines, refunds)."""
    client = ctx.get_client()
    data = client.list_card_transactions(account_id=account_id, count=count, older_id=older_id)
    echo_output(data, fmt=ctx.output_format, columns=TRANSACTION_COLUMNS)


@cards.command("transaction")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def get_transaction(ctx: Context, id: int, account_id: int | None) -> None:
    """Get a single card transaction."""
    client = ctx.get_client()
    data = client.get_card_transaction(id, account_id=account_id)
    echo_output(data, fmt=ctx.output_format)
