"""Sandbox helper commands."""

from __future__ import annotations

import click

from bunq_cli.client import create_sandbox_user
from bunq_cli.commands.login import login


@click.group()
def sandbox() -> None:
    """Sandbox environment helpers."""


@sandbox.command("create-user")
@click.option("--login", "login_profile", metavar="PROFILE", default=None, help="Log in with the new user under this profile name.")
@click.pass_context
def create_user(click_ctx: click.Context, login_profile: str | None) -> None:
    """Create a sandbox test user and print its API key."""
    api_key = create_sandbox_user()
    if login_profile:
        click_ctx.invoke(login, profile_name=login_profile, token=api_key, sandbox=True)
    else:
        click.echo(api_key)
