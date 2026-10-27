"""Tests for config module."""

import stat
import sys

import pytest

from bunq_cli.config import (
    get_credentials,
    load_config,
    remove_credentials,
    restrict_permissions,
    save_config,
    set_credentials,
)

posix_only = pytest.mark.skipif(sys.platform == "win32", reason="POSIX file modes")


@posix_only
def test_save_config_is_owner_only(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("")
    path.chmod(0o644)
    save_config({}, path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


@posix_only
def test_restrict_permissions_creates_owner_only_file(tmp_path):
    path = tmp_path / "context.conf"
    restrict_permissions(path)
    assert stat.S_IMODE(path.stat().st_mode) == 0o600


def test_restrict_permissions_ignores_os_errors(tmp_path):
    restrict_permissions(tmp_path / "missing-dir" / "file")


def test_load_nonexistent_config(tmp_path):
    path = tmp_path / "nonexistent.toml"
    assert load_config(path) == {}


def test_save_and_load_config(tmp_path):
    path = tmp_path / "config.toml"
    config = set_credentials({}, "/tmp/bunq.conf", sandbox=False)
    save_config(config, path)
    loaded = load_config(path)
    assert loaded["credentials"]["context_path"] == "/tmp/bunq.conf"
    assert loaded["credentials"]["sandbox"] == False


def test_save_sandbox_config(tmp_path):
    path = tmp_path / "config.toml"
    config = set_credentials({}, "/tmp/bunq.conf", sandbox=True)
    save_config(config, path)
    loaded = load_config(path)
    assert loaded["credentials"]["sandbox"] == True


def test_remove_credentials():
    config = set_credentials({}, "/tmp/bunq.conf")
    config = remove_credentials(config)
    assert "credentials" not in config


def test_get_credentials_empty():
    assert get_credentials({}) == {}
