"""Tests for CLI basics."""

from datetime import datetime, timedelta, timezone

import pytest

from bunq_cli.client import BunqClient
from bunq_cli.commands.scheduled import _to_api_time
from bunq_cli.main import cli


def test_version(cli_runner):
    result = cli_runner("--version")
    assert result.exit_code == 0
    assert "bunq, version" in result.output


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


@pytest.mark.parametrize(
    "group",
    ["events", "statements", "scheduled-payments", "draft-payments", "bunqme", "sandbox"],
)
def test_new_groups_help(cli_runner, group):
    result = cli_runner(group, "--help")
    assert result.exit_code == 0


def test_login_rejects_invalid_ip(cli_runner):
    result = cli_runner("login", "--token", "x", "--allowed-ip", "not-an-ip")
    assert result.exit_code != 0
    assert "not an IP address" in result.output


def test_card_update_requires_option(cli_runner):
    result = cli_runner("cards", "update", "1")
    assert result.exit_code != 0
    assert "No updates specified" in result.output


def test_callback_retry_limit(cli_runner):
    result = cli_runner("callbacks", "retry", *map(str, range(101)))
    assert result.exit_code != 0
    assert "100" in result.output


def test_scheduled_payment_to_dict():
    data = BunqClient._scheduled_payment_to_dict(
        {
            "id": 1,
            "status": "ACTIVE",
            "payment": {
                "amount": {"value": "-1.00", "currency": "EUR"},
                "counterparty_alias": {"display_name": "Landlord"},
                "description": "Rent",
            },
            "schedule": {"recurrence_unit": "MONTHLY", "recurrence_size": 1, "time_next": "2026-11-01"},
        }
    )
    assert data["counterparty"] == "Landlord"
    assert data["every"] == "1 MONTHLY"
    assert data["next"] == "2026-11-01"


def test_event_to_dict():
    data = BunqClient._event_to_dict(
        {"id": 5, "action": "CREATE", "object": {"Payment": {"id": 9}}, "monetary_account_id": "3"}
    )
    assert data["object_type"] == "Payment"
    assert data["object_id"] == 9


def test_to_api_time_is_utc():
    value = datetime(2026, 1, 1, 12, 0, tzinfo=timezone(timedelta(hours=1)))
    assert _to_api_time(value) == "2026-01-01 11:00:00"
