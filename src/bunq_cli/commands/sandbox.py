"""Sandbox helper commands."""

from __future__ import annotations

import click

from bunq_cli.client import create_sandbox_user
from bunq_cli.commands.login import login


@click.group()
def sandbox() -> None:
    """Sandbox environment helpers."""


@sandbox.command("create-user")
@click.option("--login", "do_login", is_flag=True, help="Log in with the new user (replaces your current login).")
@click.pass_context
def create_user(click_ctx: click.Context, do_login: bool) -> None:
    """Create a sandbox test user and print its API key."""
    api_key = create_sandbox_user()
    if do_login:
        click_ctx.invoke(login, token=api_key, sandbox=True)
    else:
        click.echo(api_key)
