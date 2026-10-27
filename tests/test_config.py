"""Tests for config module."""

import stat
import sys

import click
import pytest

from bunq_cli.config import (
    load_config,
    remove_profile,
    resolve_profile,
    restrict_permissions,
    save_config,
    set_profile,
    validate_profile_name,
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


def test_save_and_load_profiles(tmp_path):
    path = tmp_path / "config.toml"
    config = set_profile({}, "acme", context_path="/tmp/acme.conf", sandbox=False, display_name='Acme "B.V."')
    config = set_profile(config, "jansen", context_path="/tmp/jansen.conf", sandbox=True)
    save_config(config, path)
    loaded = load_config(path)
    assert loaded["default_profile"] == "acme"
    assert loaded["profiles"]["acme"]["display_name"] == 'Acme "B.V."'
    assert loaded["profiles"]["jansen"]["sandbox"] is True


def test_set_profile_keeps_unset_fields():
    config = set_profile({}, "acme", context_path="/tmp/a.conf", read_only=True)
    config = set_profile(config, "acme", context_path="/tmp/a.conf", read_only=None)
    assert config["profiles"]["acme"]["read_only"] is True


def test_migrates_legacy_credentials(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text('[credentials]\ncontext_path = "/tmp/bunq.conf"\nsandbox = true\n')
    config = load_config(path)
    assert "credentials" not in config
    assert config["default_profile"] == "default"
    assert config["profiles"]["default"] == {"context_path": "/tmp/bunq.conf", "sandbox": True}


def test_resolve_profile():
    config = set_profile({}, "acme", context_path="a")
    config = set_profile(config, "jansen", context_path="j")
    assert resolve_profile(config)[0] == "acme"
    assert resolve_profile(config, "jansen")[0] == "jansen"
    with pytest.raises(click.ClickException, match="Unknown profile"):
        resolve_profile(config, "nope")
    config = remove_profile(config, "acme")
    assert resolve_profile(config)[0] == "jansen"  # only one left


def test_resolve_profile_ambiguous():
    config = {"profiles": {"a": {"context_path": "a"}, "b": {"context_path": "b"}}}
    with pytest.raises(click.ClickException, match="Multiple profiles"):
        resolve_profile(config)


def test_resolve_profile_not_logged_in():
    with pytest.raises(click.ClickException, match="Not logged in"):
        resolve_profile({})


@pytest.mark.parametrize("name", ["acme", "client_1", "jansen-bv"])
def test_valid_profile_names(name):
    assert validate_profile_name(name) == name


@pytest.mark.parametrize("name", ["", "a b", "a.b", 'x"'])
def test_invalid_profile_names(name):
    with pytest.raises(click.BadParameter):
        validate_profile_name(name)
