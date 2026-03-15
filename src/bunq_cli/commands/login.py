"""Login and logout commands."""

from __future__ import annotations

import http.server
import threading
import urllib.parse
import webbrowser
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

OAUTH_REDIRECT_PORT = 12345


@click.command()
@click.option("--token", default=None, help="API key (skip OAuth and use this token directly).")
@click.option("--sandbox", is_flag=True, help="Use the sandbox environment.")
@pass_context
def login(ctx: Context, token: str | None, sandbox: bool) -> None:
    """Log in to your Bunq account.

    Without --token, opens your browser for OAuth authorization.
    With --token, uses the API key directly (for private/server use only).
    """
    sandbox = sandbox or ctx.sandbox

    if token is None:
        token = _oauth_login(sandbox)
        if token is None:
            raise click.ClickException("OAuth login failed or was cancelled.")

    context_path = str(DEFAULT_CONTEXT_PATH)
    create_context(api_key=token, context_path=Path(context_path), sandbox=sandbox)

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


def _oauth_login(sandbox: bool) -> str | None:
    """Run the OAuth browser flow and return the API token, or None on failure."""
    # TODO: Implement full OAuth flow with bunq SDK's OauthAuthorizationUri
    # For now, fall back to prompting for a token
    click.echo("OAuth login is not yet implemented.")
    click.echo("Please provide an API key using: bunq login --token YOUR_API_KEY")
    return None
