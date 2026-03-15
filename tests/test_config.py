"""Tests for config module."""

from bunq_cli.config import (
    get_credentials,
    load_config,
    remove_credentials,
    save_config,
    set_credentials,
)


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
