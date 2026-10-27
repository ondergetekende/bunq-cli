"""Login and logout commands."""

from __future__ import annotations

import ipaddress
from pathlib import Path

import click

from bunq_cli.client import create_context, current_user_name, destroy_context
from bunq_cli.config import (
    CONTEXTS_DIR,
    load_config,
    remove_profile,
    resolve_profile,
    save_config,
    set_profile,
    validate_profile_name,
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


def _validate_profile(ctx: click.Context, param: click.Parameter, value: str | None) -> str | None:
    return validate_profile_name(value) if value else None


def _contexts_dir() -> Path:
    CONTEXTS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        CONTEXTS_DIR.chmod(0o700)
    except OSError:
        pass
    return CONTEXTS_DIR


@click.command()
@click.option("--profile", "profile_name", default=None, callback=_validate_profile, help="Profile name to store this login under (e.g. the client's name).")
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
@click.option("--read-only/--read-write", default=None, help="Block commands that change data for this profile.")
@pass_context
def login(
    ctx: Context,
    profile_name: str | None,
    token: str | None,
    sandbox: bool,
    allowed_ips: list[str],
    read_only: bool | None,
) -> None:
    """Log in to a bunq account and store it as a profile.

    Without --token, opens your browser for OAuth authorization.
    With --token, uses the API key directly.
    """
    sandbox = sandbox or ctx.sandbox
    config = load_config(ctx.config_path)
    profiles = config.get("profiles", {})
    name = profile_name or ctx.profile
    if name is None and profiles:
        # Guessing could overwrite another client's login.
        raise click.UsageError(
            f"Pass --profile NAME (existing profiles: {', '.join(profiles)})."
        )
    name = validate_profile_name(name or "default")

    if token is None:
        token = oauth_login(sandbox=sandbox, config=config)

    context_path = profiles.get(name, {}).get("context_path") or str(_contexts_dir() / f"{name}.conf")
    create_context(
        api_key=token,
        context_path=Path(context_path).expanduser(),
        sandbox=sandbox,
        permitted_ips=allowed_ips,
    )

    config = set_profile(
        config,
        name,
        context_path=context_path,
        sandbox=sandbox,
        display_name=current_user_name(),
        read_only=read_only,
    )
    save_config(config, ctx.config_path)

    if not ctx.quiet:
        env_name = "sandbox" if sandbox else "production"
        who = config["profiles"][name].get("display_name") or "unknown user"
        click.echo(f"Logged in to bunq ({env_name}) as {who}, profile '{name}'.")


@click.command()
@click.option("--profile", "profile_name", default=None, help="Profile to log out (default: the selected profile).")
@click.option("--all", "all_profiles", is_flag=True, help="Log out of every profile.")
@pass_context
def logout(ctx: Context, profile_name: str | None, all_profiles: bool) -> None:
    """Close the session and remove a profile's stored credentials."""
    config = load_config(ctx.config_path)
    if all_profiles:
        names = list(config.get("profiles", {}))
    else:
        names = [resolve_profile(config, profile_name or ctx.profile)[0]]

    for name in names:
        destroy_context(Path(config["profiles"][name]["context_path"]).expanduser())
        config = remove_profile(config, name)
        if not ctx.quiet:
            click.echo(f"Logged out of profile '{name}'.")
    save_config(config, ctx.config_path)
