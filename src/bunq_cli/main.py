"""Bunq CLI - main entry point and global options."""

from __future__ import annotations

from pathlib import Path

import click
from click.core import ParameterSource

from bunq_cli.client import BunqClient
from bunq_cli.config import (
    DEFAULT_CONFIG_PATH,
    load_config,
    profile_label,
    resolve_profile,
)
from bunq_cli.output import format_output

# Commands that manage profiles/credentials themselves and make no sense per profile.
SINGLE_PROFILE_COMMANDS = {"login", "logout", "profiles", "sandbox", "oauth-client"}


class Context:
    """Shared context for all commands."""

    def __init__(self) -> None:
        self.verbose: bool = False
        self.quiet: bool = False
        self.output_format: str = "auto"
        self.no_color: bool = False
        self.sandbox: bool = False
        self.config_path: Path = DEFAULT_CONFIG_PATH
        self.token: str | None = None
        self.profile: str | None = None
        self.all_profiles: bool = False
        self.profile_name: str | None = None
        self.profile_label: str = ""
        # Set when running one profile of an --all-profiles invocation.
        self.loop_profile: str | None = None
        self.collected: list[tuple[object, list[str] | None]] | None = None

    def get_client(self, write: bool = False, profile: str | None = None) -> BunqClient:
        """Build a BunqClient for the selected profile.

        ``write`` marks commands that change data: they are refused for
        read-only profiles and with --all-profiles.
        """
        if write and self.all_profiles:
            raise click.UsageError("This command changes data and can't be used with --all-profiles.")
        name, settings = resolve_profile(load_config(self.config_path), profile or self.profile)
        if write and settings.get("read_only"):
            raise click.ClickException(f"Profile '{name}' is read-only.")
        self.profile_name = name
        self.profile_label = profile_label(name, settings)
        if self.verbose:
            click.echo(f"Using profile {self.profile_label}", err=True)

        return BunqClient(
            context_path=Path(settings["context_path"]).expanduser(),
            sandbox=self.sandbox or settings.get("sandbox", False),
            verbose=self.verbose,
        )

    def confirm(self, message: str, yes: bool) -> None:
        """Ask for confirmation, naming the profile so clients aren't mixed up."""
        if not yes:
            click.confirm(f"[{self.profile_label}] {message}", abort=True)


pass_context = click.make_pass_decorator(Context, ensure=True)
yes_option = click.option("--yes", "-y", is_flag=True, help="Don't ask for confirmation.")


class _CliGroup(click.Group):
    def parse_args(self, ctx: click.Context, args: list[str]) -> list[str]:
        ctx.meta["bunq.argv"] = list(args)
        return super().parse_args(ctx, args)


def _run_for_all_profiles(ctx: Context) -> None:
    """Re-run the command line once per profile and merge the output."""
    click_ctx = click.get_current_context()
    if click_ctx.invoked_subcommand in SINGLE_PROFILE_COMMANDS:
        raise click.UsageError(f"'{click_ctx.invoked_subcommand}' can't be used with --all-profiles.")
    profiles = load_config(ctx.config_path).get("profiles", {})
    if not profiles:
        raise click.ClickException("Not logged in. Run 'bunq login' first.")

    rows: list[dict] = []
    columns: list[str] | None = None
    failed = False
    for name, settings in profiles.items():
        if not ctx.quiet:
            click.echo(f"== {profile_label(name, settings)} ==", err=True)
        sub = Context()
        sub.loop_profile = name
        sub.collected = []
        try:
            cli.main(
                args=click_ctx.meta["bunq.argv"],
                prog_name=click_ctx.info_name,
                standalone_mode=False,
                obj=sub,
            )
        except (click.UsageError, click.Abort):
            raise
        except Exception as exc:  # one client's failure shouldn't stop the others
            failed = True
            message = exc.format_message() if isinstance(exc, click.ClickException) else str(exc)
            click.echo(f"Error ({name}): {message}", err=True)
            continue
        for data, cols in sub.collected:
            records = data if isinstance(data, list) else [data]
            rows += [{"profile": name, **record} for record in records]
            columns = columns or cols

    if rows:
        click.echo(
            format_output(rows, fmt=ctx.output_format, columns=["profile", *columns] if columns else None)
        )
    click_ctx.exit(1 if failed else 0)


@click.group(cls=_CliGroup)
@click.version_option(version="0.1.0", prog_name="bunq")
@click.option("-v", "--verbose", is_flag=True, help="Enable verbose output.")
@click.option("-q", "--quiet", is_flag=True, help="Suppress all output except errors.")
@click.option("--token", metavar="TOKEN", help="API token (overrides stored credentials).")
@click.option(
    "--output",
    "output_format",
    type=click.Choice(["auto", "json", "table"]),
    default="auto",
    help="Output format.",
)
@click.option("--no-color", is_flag=True, help="Disable colored output.")
@click.option(
    "--config",
    "config_path",
    type=click.Path(path_type=Path),
    default=None,
    help="Custom config file path.",
)
@click.option("--sandbox", is_flag=True, help="Use the sandbox environment.")
@click.option("-p", "--profile", envvar="BUNQ_PROFILE", default=None, help="Profile (client) to use. Env: BUNQ_PROFILE.")
@click.option("--all-profiles", is_flag=True, help="Run a read-only command for every profile.")
@pass_context
def cli(
    ctx: Context,
    verbose: bool,
    quiet: bool,
    token: str | None,
    output_format: str,
    no_color: bool,
    config_path: Path | None,
    sandbox: bool,
    profile: str | None,
    all_profiles: bool,
) -> None:
    """Bunq CLI - interact with the Bunq API from your terminal."""
    ctx.verbose = verbose
    ctx.quiet = quiet
    ctx.output_format = output_format
    ctx.no_color = no_color
    ctx.sandbox = sandbox
    ctx.token = token
    ctx.profile = ctx.loop_profile or profile
    ctx.all_profiles = all_profiles
    if config_path:
        ctx.config_path = config_path
    if all_profiles:
        source = click.get_current_context().get_parameter_source("profile")
        if source == ParameterSource.COMMANDLINE:
            raise click.UsageError("Use either --profile or --all-profiles, not both.")
        ctx.profile = ctx.loop_profile
    if all_profiles and ctx.loop_profile is None:
        _run_for_all_profiles(ctx)


# Register commands
from bunq_cli.commands.login import login, logout  # noqa: E402
from bunq_cli.commands.accounts import accounts  # noqa: E402
from bunq_cli.commands.payments import payments  # noqa: E402
from bunq_cli.commands.requests import requests  # noqa: E402
from bunq_cli.commands.cards import cards  # noqa: E402
from bunq_cli.commands.callbacks import callbacks  # noqa: E402
from bunq_cli.commands.oauth_client import oauth_client  # noqa: E402
from bunq_cli.commands.events import events  # noqa: E402
from bunq_cli.commands.statements import statements  # noqa: E402
from bunq_cli.commands.scheduled import scheduled  # noqa: E402
from bunq_cli.commands.drafts import drafts  # noqa: E402
from bunq_cli.commands.bunqme import bunqme  # noqa: E402
from bunq_cli.commands.sandbox import sandbox  # noqa: E402
from bunq_cli.commands.profiles import profiles  # noqa: E402

cli.add_command(login)
cli.add_command(logout)
cli.add_command(accounts)
cli.add_command(payments)
cli.add_command(requests)
cli.add_command(cards)
cli.add_command(callbacks)
cli.add_command(oauth_client)
cli.add_command(events)
cli.add_command(statements)
cli.add_command(scheduled)
cli.add_command(drafts)
cli.add_command(bunqme)
cli.add_command(sandbox)
cli.add_command(profiles)
