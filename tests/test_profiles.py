"""Tests for profile handling."""

import pytest

from bunq_cli.config import load_config, save_config, set_profile

PAY_ARGS = [
    "payments", "create", "--amount", "1.00", "--recipient-iban", "NL00BUNQ0000000000",
    "--recipient-name", "X", "--description", "x", "--yes",
]


@pytest.fixture
def two_profiles(cli_runner, tmp_path):
    config = set_profile({}, "acme", context_path=str(tmp_path / "acme.conf"), display_name="Acme B.V.")
    config = set_profile(config, "jansen", context_path=str(tmp_path / "jansen.conf"), read_only=True)
    save_config(config, cli_runner.config_path)
    return cli_runner


def test_profiles_list(two_profiles):
    result = two_profiles("--output", "json", "profiles", "list")
    assert result.exit_code == 0
    assert '"name": "acme"' in result.output
    assert '"read_only": true' in result.output


def test_profiles_use_and_rename(two_profiles):
    assert two_profiles("profiles", "use", "jansen").exit_code == 0
    assert two_profiles("profiles", "rename", "jansen", "jansen-bv").exit_code == 0
    config = load_config(two_profiles.config_path)
    assert config["default_profile"] == "jansen-bv"
    assert "jansen" not in config["profiles"]


def test_profiles_use_unknown(two_profiles):
    result = two_profiles("profiles", "use", "nope")
    assert result.exit_code != 0
    assert "Unknown profile" in result.output


def test_read_only_profile_blocks_writes(two_profiles):
    result = two_profiles("--profile", "jansen", "cards", "freeze", "1")
    assert result.exit_code != 0
    assert "read-only" in result.output


def test_all_profiles_blocks_writes(two_profiles):
    result = two_profiles("--all-profiles", *PAY_ARGS)
    assert result.exit_code == 2
    assert "can't be used with --all-profiles" in result.output


def test_all_profiles_blocks_login(two_profiles):
    result = two_profiles("--all-profiles", "login", "--token", "x")
    assert result.exit_code == 2


def test_all_profiles_reports_each_failure(two_profiles):
    result = two_profiles("--all-profiles", "accounts", "list")
    assert result.exit_code == 1
    assert "== Acme B.V. (acme) ==" in result.output
    assert "Error (acme)" in result.output
    assert "Error (jansen)" in result.output


def test_all_profiles_with_explicit_profile(two_profiles):
    result = two_profiles("--all-profiles", "--profile", "acme", "accounts", "list")
    assert result.exit_code == 2


def test_login_requires_profile_name_when_profiles_exist(two_profiles):
    result = two_profiles("login", "--token", "x")
    assert result.exit_code == 2
    assert "acme, jansen" in result.output


def test_login_rejects_bad_profile_name(cli_runner):
    result = cli_runner("login", "--profile", "a b", "--token", "x")
    assert result.exit_code == 2
