"""Account statement export commands."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import click

from bunq_cli.main import Context, pass_context
from bunq_cli.output import echo_output

LIST_COLUMNS = ["id", "created", "date_start", "date_end", "format", "status"]


@click.group()
def statements() -> None:
    """Export account statements."""


@statements.command("list")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def list_statements(ctx: Context, account_id: int | None) -> None:
    """List statement exports."""
    client = ctx.get_client()
    data = client.list_statements(account_id=account_id)
    echo_output(data, fmt=ctx.output_format, columns=LIST_COLUMNS)


@statements.command("create")
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("--from", "date_start", required=True, type=click.DateTime(["%Y-%m-%d"]), help="Start date (YYYY-MM-DD).")
@click.option("--to", "date_end", required=True, type=click.DateTime(["%Y-%m-%d"]), help="End date (YYYY-MM-DD).")
@click.option(
    "--format",
    "statement_format",
    type=click.Choice(["CSV", "PDF", "MT940"], case_sensitive=False),
    default="CSV",
    help="Statement format (default: CSV).",
)
@click.option(
    "--regional-format",
    type=click.Choice(["EUROPEAN", "UK_US"], case_sensitive=False),
    default="EUROPEAN",
    help="CSV separator style: EUROPEAN (;) or UK_US (,). Only used for CSV.",
)
@pass_context
def create_statement(
    ctx: Context,
    account_id: int | None,
    date_start: datetime,
    date_end: datetime,
    statement_format: str,
    regional_format: str,
) -> None:
    """Request a statement export. Download it with 'statements download'."""
    statement_format = statement_format.upper()
    client = ctx.get_client()
    statement_id = client.create_statement(
        statement_format=statement_format,
        date_start=date_start.strftime("%Y-%m-%d"),
        date_end=date_end.strftime("%Y-%m-%d"),
        regional_format=regional_format.upper() if statement_format == "CSV" else None,
        account_id=account_id,
    )
    if not ctx.quiet:
        click.echo(f"Statement export created (ID: {statement_id}).")


@statements.command("download")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@click.option("-o", "--output-file", type=click.Path(path_type=Path, dir_okay=False), required=True, help="File to write the statement to.")
@pass_context
def download_statement(ctx: Context, id: int, account_id: int | None, output_file: Path) -> None:
    """Download a statement export."""
    client = ctx.get_client()
    if ctx.all_profiles:
        if "{profile}" not in str(output_file):
            raise click.UsageError("With --all-profiles, put {profile} in the output file name.")
        output_file = Path(str(output_file).replace("{profile}", ctx.profile_name))
    output_file.write_bytes(client.download_statement(id, account_id=account_id))
    if not ctx.quiet:
        click.echo(f"Statement saved to {output_file}.")


@statements.command("delete")
@click.argument("id", type=int)
@click.option("--account", "account_id", type=int, default=None, help="Monetary account ID (default: primary).")
@pass_context
def delete_statement(ctx: Context, id: int, account_id: int | None) -> None:
    """Delete a statement export."""
    client = ctx.get_client(write=True)
    client.delete_statement(id, account_id=account_id)
    if not ctx.quiet:
        click.echo(f"Statement {id} deleted.")
