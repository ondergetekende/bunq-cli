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
@pass_context
def update_card(ctx: Context, id: int, daily_limit: float | None) -> None:
    """Update card settings."""
    kwargs = {}
    if daily_limit is not None:
        from bunq.sdk.model.generated.object_ import AmountObject
        kwargs["card_limit"] = AmountObject(f"{daily_limit:.2f}", "EUR")

    if not kwargs:
        raise click.ClickException("No updates specified. Use --daily-limit.")

    client = ctx.get_client()
    data = client.update_card(id, **kwargs)
    echo_output(data, fmt=ctx.output_format)
