"""OAuth client management commands."""

from __future__ import annotations

import click
from bunq.sdk.model.generated.endpoint import (
    OauthCallbackUrlApiObject,
    OauthClientApiObject,
)

from bunq_cli.config import (
    get_oauth_client,
    load_config,
    remove_oauth_client,
    save_config,
    set_oauth_client,
)
from bunq_cli.main import Context, pass_context, yes_option
from bunq_cli.oauth import REDIRECT_URI
from bunq_cli.output import echo_output


@click.group(name="oauth-client")
def oauth_client() -> None:
    """Manage the OAuth client for browser-based login."""


@oauth_client.command("register")
@pass_context
def register(ctx: Context) -> None:
    """Register a new OAuth client and store its credentials.

    Requires an active session (run 'bunq login --token' first); the OAuth
    client is owned by the selected profile's user.
    Automatically adds the CLI callback URL.
    """
    client = ctx.get_client(write=True)  # noqa: F841 -- ensures SDK context is loaded

    config = load_config(ctx.config_path)
    existing = get_oauth_client(config)
    if existing.get("client_id"):
        raise click.ClickException(
            "An OAuth client is already registered. "
            "Run 'bunq oauth-client delete' first to replace it."
        )

    # Create the OAuth client
    response = OauthClientApiObject.create(status="ACTIVE")
    oauth_id = response.value

    # Fetch the client details (client_id + secret)
    detail = OauthClientApiObject.get(oauth_id).value
    client_id = detail.client_id
    client_secret = detail.secret

    # Register the CLI callback URL
    OauthCallbackUrlApiObject.create(oauth_id, url=REDIRECT_URI)

    # Persist to config
    config = set_oauth_client(config, client_id, client_secret, oauth_id, ctx.profile_name)
    save_config(config, ctx.config_path)

    if not ctx.quiet:
        click.echo(f"OAuth client registered (ID: {oauth_id}).")
        click.echo(f"Client ID:     {client_id}")
        click.echo(f"Callback URL:  {REDIRECT_URI}")
        click.echo()
        click.echo("You can now log in with: bunq login")


@oauth_client.command("show")
@pass_context
def show(ctx: Context) -> None:
    """Show the stored OAuth client credentials."""
    config = load_config(ctx.config_path)
    oauth = get_oauth_client(config)
    if not oauth.get("client_id"):
        raise click.ClickException(
            "No OAuth client registered. Run 'bunq oauth-client register' first."
        )
    data = {
        "oauth_client_id": oauth["oauth_client_id"],
        "client_id": oauth["client_id"],
        "client_secret": oauth["client_secret"],
        "callback_url": REDIRECT_URI,
        "profile": oauth.get("profile", ""),
    }
    echo_output(data, fmt=ctx.output_format)


@oauth_client.command("delete")
@yes_option
@pass_context
def delete(ctx: Context, yes: bool) -> None:
    """Delete the OAuth client and remove stored credentials."""
    config = load_config(ctx.config_path)
    oauth = get_oauth_client(config)
    oauth_id = oauth.get("oauth_client_id")
    # The OAuth client lives under the user that registered it.
    client = ctx.get_client(write=True, profile=oauth.get("profile"))  # noqa: F841
    ctx.confirm("Delete the OAuth client?", yes)

    if oauth_id:
        try:
            OauthClientApiObject.update(oauth_id, status="CANCELLED")
        except Exception:
            pass  # best-effort: client may already be gone

    config = remove_oauth_client(config)
    save_config(config, ctx.config_path)

    if not ctx.quiet:
        click.echo("OAuth client deleted.")
