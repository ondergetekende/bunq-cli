"""Configuration management for Bunq CLI."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import click

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "bunq-cli.toml"
DEFAULT_CONTEXT_PATH = Path.home() / ".config" / "bunq-cli.conf"
CONTEXTS_DIR = Path.home() / ".config" / "bunq-cli" / "contexts"
PROFILE_NAME_RE = re.compile(r"^[A-Za-z0-9_-]+$")


def _serialize_toml(data: dict, prefix: str = "") -> str:
    """Serialize a dict to TOML format (minimal implementation)."""
    lines: list[str] = []
    for key, value in data.items():
        if not isinstance(value, dict):
            lines.append(f"{key} = {_toml_value(value)}")
    for key, value in data.items():
        if isinstance(value, dict):
            full_key = f"{prefix}.{key}" if prefix else key
            has_subtables = any(isinstance(v, dict) for v in value.values())
            if has_subtables:
                scalars = {k: v for k, v in value.items() if not isinstance(v, dict)}
                if scalars:
                    lines.append("")
                    lines.append(f"[{full_key}]")
                    for k, v in scalars.items():
                        lines.append(f"{k} = {_toml_value(v)}")
                subtables = {k: v for k, v in value.items() if isinstance(v, dict)}
                lines.append(_serialize_toml(subtables, prefix=full_key))
            else:
                lines.append("")
                lines.append(f"[{full_key}]")
                for k, v in value.items():
                    lines.append(f"{k} = {_toml_value(v)}")
    return "\n".join(lines)


def _toml_value(value: object) -> str:
    if isinstance(value, str):
        # JSON string escapes are valid TOML basic-string escapes.
        return json.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    raise TypeError(f"Unsupported TOML value type: {type(value)}")


def load_config(path: Path | None = None) -> dict:
    """Load configuration from TOML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.exists():
        return {}
    with open(config_path, "rb") as f:
        return _migrate(tomllib.load(f))


def _migrate(config: dict) -> dict:
    """Turn the pre-profiles [credentials] section into a 'default' profile."""
    creds = config.pop("credentials", None)
    if creds and "profiles" not in config:
        config["profiles"] = {
            "default": {
                "context_path": creds.get("context_path", str(DEFAULT_CONTEXT_PATH)),
                "sandbox": creds.get("sandbox", False),
            }
        }
        config.setdefault("default_profile", "default")
    return config


def restrict_permissions(path: Path) -> None:
    """Best effort: create/chmod a credential file so only the owner can read it."""
    try:
        path.touch(mode=0o600, exist_ok=True)
        path.chmod(0o600)
    except OSError:
        pass


def save_config(data: dict, path: Path | None = None) -> None:
    """Save configuration to TOML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
    restrict_permissions(config_path)
    config_path.write_text(_serialize_toml(data) + "\n")


def validate_profile_name(name: str) -> str:
    if not PROFILE_NAME_RE.match(name):
        raise click.BadParameter(
            f"Invalid profile name {name!r}: use letters, digits, '-' and '_'."
        )
    return name


def profile_label(name: str, profile: dict) -> str:
    display_name = profile.get("display_name")
    return f"{display_name} ({name})" if display_name else name


def resolve_profile(config: dict, name: str | None = None) -> tuple[str, dict]:
    """Return (name, profile) for the requested, default or only profile."""
    profiles = config.get("profiles", {})
    if not profiles:
        raise click.ClickException("Not logged in. Run 'bunq login' first.")
    if name is None:
        name = config.get("default_profile")
    if name is None and len(profiles) == 1:
        name = next(iter(profiles))
    if name is None:
        raise click.ClickException(
            "Multiple profiles configured. Pass --profile NAME or run 'bunq profiles use NAME'."
        )
    if name not in profiles:
        raise click.ClickException(
            f"Unknown profile '{name}'. Run 'bunq profiles list' to see the available profiles."
        )
    return name, profiles[name]


def set_profile(config: dict, name: str, **fields: object) -> dict:
    """Create or update a profile; fields set to None are left unchanged."""
    profile = config.setdefault("profiles", {}).setdefault(name, {})
    profile.update({k: v for k, v in fields.items() if v is not None})
    config.setdefault("default_profile", name)
    return config


def remove_profile(config: dict, name: str) -> dict:
    config.get("profiles", {}).pop(name, None)
    if not config.get("profiles"):
        config.pop("profiles", None)
    if config.get("default_profile") == name:
        config.pop("default_profile")
    return config


def get_oauth_client(config: dict) -> dict:
    """Get stored OAuth client credentials."""
    return config.get("oauth", {})


def set_oauth_client(
    config: dict,
    client_id: str,
    client_secret: str,
    oauth_client_id: int,
    profile: str,
) -> dict:
    """Set OAuth client credentials in config."""
    config["oauth"] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "oauth_client_id": oauth_client_id,
        "profile": profile,
    }
    return config


def remove_oauth_client(config: dict) -> dict:
    """Remove stored OAuth client credentials."""
    config.pop("oauth", None)
    return config
