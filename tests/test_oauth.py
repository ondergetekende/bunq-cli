"""Tests for OAuth module."""

from __future__ import annotations

import http.client
import threading
import urllib.parse

import pytest

from bunq_cli.oauth import (
    REDIRECT_HOST,
    REDIRECT_PORT,
    get_oauth_credentials,
    oauth_login,
)


def test_get_oauth_credentials_missing(monkeypatch):
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_SECRET", raising=False)
    assert get_oauth_credentials() is None


def test_get_oauth_credentials_present(monkeypatch):
    monkeypatch.setenv("BUNQ_OAUTH_CLIENT_ID", "test-id")
    monkeypatch.setenv("BUNQ_OAUTH_CLIENT_SECRET", "test-secret")
    creds = get_oauth_credentials()
    assert creds is not None
    assert creds.client_id == "test-id"
    assert creds.client_secret == "test-secret"


def test_get_oauth_credentials_partial(monkeypatch):
    monkeypatch.setenv("BUNQ_OAUTH_CLIENT_ID", "test-id")
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_SECRET", raising=False)
    assert get_oauth_credentials() is None


def test_get_oauth_credentials_from_config(monkeypatch):
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_SECRET", raising=False)
    config = {"oauth": {"client_id": "cfg-id", "client_secret": "cfg-secret"}}
    creds = get_oauth_credentials(config)
    assert creds is not None
    assert creds.client_id == "cfg-id"
    assert creds.client_secret == "cfg-secret"


def test_env_overrides_config(monkeypatch):
    monkeypatch.setenv("BUNQ_OAUTH_CLIENT_ID", "env-id")
    monkeypatch.setenv("BUNQ_OAUTH_CLIENT_SECRET", "env-secret")
    config = {"oauth": {"client_id": "cfg-id", "client_secret": "cfg-secret"}}
    creds = get_oauth_credentials(config)
    assert creds.client_id == "env-id"


def test_oauth_login_fails_without_credentials(monkeypatch):
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_ID", raising=False)
    monkeypatch.delenv("BUNQ_OAUTH_CLIENT_SECRET", raising=False)
    with pytest.raises(Exception, match="OAuth client not configured"):
        oauth_login(sandbox=False)
