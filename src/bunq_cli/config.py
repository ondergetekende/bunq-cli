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


def save_config(data: dict, path: Path | None = None) -> None:
    """Save configuration to TOML file."""
    config_path = path or DEFAULT_CONFIG_PATH
    config_path.parent.mkdir(parents=True, exist_ok=True)
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
