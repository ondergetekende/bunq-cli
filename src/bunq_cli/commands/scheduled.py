"""Scheduled payment commands."""

from __future__ import annotations

from datetime import datetime, timezone

import click

from bunq_cli.main import Context, pass_context, yes_option
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "status", "amount", "currency", "counterparty", "description", "every", "next"]
UNITS = ["ONCE", "HOURLY", "DAILY", "WEEKLY", "MONTHLY", "YEARLY"]
DATETIME_FORMATS = ["%Y-%m-%d", "%Y-%m-%d %H:%M", "%Y-%m-%dT%H:%M"]


def _to_api_time(value: datetime) -> str:
    # bunq expects UTC; naive input is treated as local time.
    return value.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


@click.group("scheduled-payments")
def scheduled() -> None:
    """Manage scheduled (recurring) payments."""


@scheduled.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def list_scheduled(ctx: Context, account_id: int | None) -> None:
    """List scheduled payments."""
    client = ctx.get_client()
    data = client.list_scheduled_payments(account_id=account_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@scheduled.command("get")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def get_scheduled(ctx: Context, id: int, account_id: int | None) -> None:
    """Get a single scheduled payment."""
    client = ctx.get_client()
    data = client.get_scheduled_payment(id, account_id=account_id)
    echo_output(data, fmt=ctx.output_format)


@scheduled.command("create")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--amount", required=True, help="Amount per payment (e.g., 25.00).")
@click.option("--currency", default="EUR", help="Currency code (default: EUR).")
@click.option("--recipient-iban", required=True, help="Recipient IBAN.")
@click.option("--recipient-name", required=True, help="Recipient name.")
@click.option("--description", required=True, help="Payment description.")
@click.option("--schedule-date", "start", required=True, type=click.DateTime(DATETIME_FORMATS), help="First payment (local time, e.g. 2026-11-01 or '2026-11-01 09:00').")
@click.option("--end-date", "end", type=click.DateTime(DATETIME_FORMATS), default=None, help="Stop after this date (optional).")
@click.option("--frequency", "unit", type=click.Choice(UNITS, case_sensitive=False), default="ONCE", help="How often to pay (default: ONCE).")
@click.option("--every", type=click.IntRange(min=1), default=1, help="Repeat every N periods, e.g. --every 2 --frequency WEEKLY.")
@yes_option
@pass_context
def create_scheduled(
    ctx: Context,
    account_id: int | None,
    amount: str,
    currency: str,
    recipient_iban: str,
    recipient_name: str,
    description: str,
    start: datetime,
    end: datetime | None,
    unit: str,
    every: int,
    yes: bool,
) -> None:
    """Schedule a (recurring) payment."""
    client = ctx.get_client(write=True)
    source = f"account {account_id}" if account_id else "the primary account"
    ctx.confirm(
        f"Schedule {amount} {currency} to {recipient_name} ({recipient_iban}) from {source}, "
        f"starting {start:%Y-%m-%d %H:%M}, {unit.upper()}?",
        yes,
    )
    schedule_id = client.create_scheduled_payment(
        amount=amount,
        currency=currency,
        recipient_iban=recipient_iban,
        recipient_name=recipient_name,
        description=description,
        time_start=_to_api_time(start),
        time_end=_to_api_time(end) if end else None,
        recurrence_unit=unit.upper(),
        recurrence_size=every,
        account_id=account_id,
    )
    if not ctx.quiet:
        click.echo(f"Scheduled payment created (ID: {schedule_id}).")


@scheduled.command("delete")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def cancel_scheduled(ctx: Context, id: int, account_id: int | None) -> None:
    """Cancel a scheduled payment."""
    client = ctx.get_client(write=True)
    client.cancel_scheduled_payment(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"Scheduled payment {id} cancelled.")
