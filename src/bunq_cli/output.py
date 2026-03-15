"""Output formatting for Bunq CLI."""

from __future__ import annotations

import json
import sys
from typing import Any

import click
from tabulate import tabulate


def format_output(
    data: Any,
    fmt: str = "auto",
    columns: list[str] | None = None,
) -> str:
    """Format data for output.

    Args:
        data: The data to format (dict or list of dicts).
        fmt: Output format - "json", "table", or "auto".
        columns: Column names to include in table output. If None, uses all keys.
    """
    if fmt == "auto":
        fmt = "table" if sys.stdout.isatty() else "json"

    if fmt == "json":
        return json.dumps(data, indent=2, default=str)

    if isinstance(data, dict):
        rows = [[k, v] for k, v in data.items() if columns is None or k in columns]
        return tabulate(rows, headers=["Field", "Value"], tablefmt="simple")

    if isinstance(data, list) and data:
        if columns is None:
            columns = list(data[0].keys())
        rows = [[record.get(col, "") for col in columns] for record in data]
        return tabulate(rows, headers=columns, tablefmt="simple")

    return str(data)


def echo_output(
    data: Any,
    fmt: str = "auto",
    columns: list[str] | None = None,
) -> None:
    """Format and print data."""
    if data is None:
        return
    output = format_output(data, fmt=fmt, columns=columns)
    click.echo(output)
