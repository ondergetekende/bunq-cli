"""Profile (client) management commands."""

from __future__ import annotations

from pathlib import Path

import click

from bunq_cli.config import (
    load_config,
    resolve_profile,
    save_config,
    validate_profile_name,
)
from bunq_cli.main import Context, complete_profile, pass_context
from bunq_cli.output import echo_output


@click.group()
def profiles() -> None:
    """Manage profiles (one per bunq login, e.g. per client)."""


@profiles.command("list")
@pass_context
def list_profiles(ctx: Context) -> None:
    """List profiles."""
    config = load_config(ctx.config_path)
    default = config.get("default_profile")
    data = [
        {
            "default": "*" if name == default else "",
            "name": name,
            "display_name": p.get("display_name", ""),
            "environment": "sandbox" if p.get("sandbox") else "production",
            "read_only": p.get("read_only", False),
            "logged_in": Path(p["context_path"]).expanduser().exists(),
        }
        for name, p in config.get("profiles", {}).items()
    ]
    echo_output(data, fmt=ctx.output_format)


@profiles.command("use")
@click.argument("name", shell_complete=complete_profile)
@pass_context
def use_profile(ctx: Context, name: str) -> None:
    """Set the default profile."""
    config = load_config(ctx.config_path)
    resolve_profile(config, name)
    config["default_profile"] = name
    save_config(config, ctx.config_path)
    if not ctx.quiet:
        click.echo(f"Default profile is now '{name}'.")


@profiles.command("rename")
@click.argument("old", shell_complete=complete_profile)
@click.argument("new")
@pass_context
def rename_profile(ctx: Context, old: str, new: str) -> None:
    """Rename a profile."""
    validate_profile_name(new)
    config = load_config(ctx.config_path)
    resolve_profile(config, old)
    if new in config["profiles"]:
        raise click.ClickException(f"Profile '{new}' already exists.")
    config["profiles"][new] = config["profiles"].pop(old)
    if config.get("default_profile") == old:
        config["default_profile"] = new
    if config.get("oauth", {}).get("profile") == old:
        config["oauth"]["profile"] = new
    save_config(config, ctx.config_path)
    if not ctx.quiet:
        click.echo(f"Profile '{old}' renamed to '{new}'.")


@profiles.command("set")
@click.argument("name", shell_complete=complete_profile)
@click.option("--read-only/--read-write", default=None, help="Block or allow commands that change data.")
@pass_context
def set_profile_options(ctx: Context, name: str, read_only: bool | None) -> None:
    """Change profile settings."""
    if read_only is None:
        raise click.ClickException("Nothing to change. Use --read-only or --read-write.")
    config = load_config(ctx.config_path)
    resolve_profile(config, name)
    config["profiles"][name]["read_only"] = read_only
    save_config(config, ctx.config_path)
    if not ctx.quiet:
        click.echo(f"Profile '{name}' is now {'read-only' if read_only else 'read-write'}.")
