"""Login and logout commands."""

from __future__ import annotations

import ipaddress
from pathlib import Path

import click

from bunq_cli.client import create_context, destroy_context
from bunq_cli.config import (
    DEFAULT_CONTEXT_PATH,
    load_config,
    remove_credentials,
    save_config,
    set_credentials,
)
from bunq_cli.main import Context, pass_context
from bunq_cli.oauth import oauth_login


def _validate_ips(ctx: click.Context, param: click.Parameter, value: tuple[str, ...]) -> list[str]:
    for ip in value:
        if ip != "*":
            try:
                ipaddress.ip_address(ip)
            except ValueError:
                raise click.BadParameter(f"{ip!r} is not an IP address or '*'.") from None
    return list(value)


@click.command()
@click.option("--token", default=None, help="API key (skip OAuth and use this token directly).")
@click.option("--sandbox", is_flag=True, help="Use the sandbox environment.")
@click.option(
    "--allowed-ip",
    "allowed_ips",
    multiple=True,
    default=["*"],
    show_default=True,
    callback=_validate_ips,
    help="IP address the API key may be used from (repeatable). With '*', bunq assigns "
    "the IP you log in from, or allows any IP for wildcard API keys.",
)
@pass_context
def login(ctx: Context, token: str | None, sandbox: bool, allowed_ips: list[str]) -> None:
    """Log in to your Bunq account.

    Without --token, opens your browser for OAuth authorization.
    With --token, uses the API key directly (for private/server use only).
    """
    sandbox = sandbox or ctx.sandbox

    if token is None:
        config = load_config(ctx.config_path)
        token = oauth_login(sandbox=sandbox, config=config)

    context_path = str(DEFAULT_CONTEXT_PATH)
    create_context(
        api_key=token,
        context_path=Path(context_path),
        sandbox=sandbox,
        permitted_ips=allowed_ips,
    )

    config = load_config(ctx.config_path)
    config = set_credentials(config, context_path=context_path, sandbox=sandbox)
    save_config(config, ctx.config_path)

    env_name = "sandbox" if sandbox else "production"
    if not ctx.quiet:
        click.echo(f"Logged in to Bunq ({env_name}).")


@click.command()
@pass_context
def logout(ctx: Context) -> None:
    """Log out by removing stored credentials and closing the session."""
    config = load_config(ctx.config_path)
    creds = config.get("credentials", {})
    context_path = creds.get("context_path", str(DEFAULT_CONTEXT_PATH))
    destroy_context(Path(context_path))

    config = remove_credentials(config)
    save_config(config, ctx.config_path)
    if not ctx.quiet:
        click.echo("Logged out.")
