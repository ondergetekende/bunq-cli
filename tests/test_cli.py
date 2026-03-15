"""Tests for CLI basics."""

from bunq_cli.main import cli


def test_version(cli_runner):
    result = cli_runner("--version")
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_help(cli_runner):
    result = cli_runner("--help")
    assert result.exit_code == 0
    assert "Bunq CLI" in result.output


def test_accounts_help(cli_runner):
    result = cli_runner("accounts", "--help")
    assert result.exit_code == 0
    assert "monetary accounts" in result.output.lower()


def test_payments_help(cli_runner):
    result = cli_runner("payments", "--help")
    assert result.exit_code == 0
    assert "payments" in result.output.lower()


def test_cards_help(cli_runner):
    result = cli_runner("cards", "--help")
    assert result.exit_code == 0
    assert "cards" in result.output.lower()


def test_requests_help(cli_runner):
    result = cli_runner("requests", "--help")
    assert result.exit_code == 0
    assert "payment requests" in result.output.lower()


def test_callbacks_help(cli_runner):
    result = cli_runner("callbacks", "--help")
    assert result.exit_code == 0
    assert "notification" in result.output.lower()
