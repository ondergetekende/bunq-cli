"""Configuration management for Bunq CLI."""

from __future__ import annotations

import sys
from pathlib import Path

if sys.version_info >= (3, 11):
    import tomllib
else:
    try:
        import tomllib
    except ModuleNotFoundError:
        import tomli as tomllib  # type: ignore[no-redef]


DEFAULT_CONFIG_PATH = Path.home() / ".config" / "bunq-cli.toml"
DEFAULT_CONTEXT_PATH = Path.home() / ".config" / "bunq-cli.conf"


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
        return f'"{value}"'
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
        return tomllib.load(f)


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


def get_credentials(config: dict) -> dict:
    """Get stored credentials."""
    return config.get("credentials", {})


def set_credentials(
    config: dict,
    context_path: str,
    sandbox: bool = False,
) -> dict:
    """Set credentials in config."""
    config["credentials"] = {
        "context_path": context_path,
        "sandbox": sandbox,
    }
    return config


def remove_credentials(config: dict) -> dict:
    """Remove stored credentials."""
    config.pop("credentials", None)
    return config


def get_oauth_client(config: dict) -> dict:
    """Get stored OAuth client credentials."""
    return config.get("oauth", {})


def set_oauth_client(
    config: dict,
    client_id: str,
    client_secret: str,
    oauth_client_id: int,
) -> dict:
    """Set OAuth client credentials in config."""
    config["oauth"] = {
        "client_id": client_id,
        "client_secret": client_secret,
        "oauth_client_id": oauth_client_id,
    }
    return config


def remove_oauth_client(config: dict) -> dict:
    """Remove stored OAuth client credentials."""
    config.pop("oauth", None)
    return config
