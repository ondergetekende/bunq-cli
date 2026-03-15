"""OAuth authorization code flow for Bunq CLI."""

from __future__ import annotations

import http.server
import os
import secrets
import threading
import urllib.parse
import webbrowser
from dataclasses import dataclass

import click
import requests

AUTH_URL_PRODUCTION = "https://oauth.bunq.com/auth"
AUTH_URL_SANDBOX = "https://oauth.sandbox.bunq.com/auth"
TOKEN_URL_PRODUCTION = "https://api.oauth.bunq.com/v1/token"
TOKEN_URL_SANDBOX = "https://api-oauth.sandbox.bunq.com/v1/token"

REDIRECT_HOST = "127.0.0.1"
REDIRECT_PORT = 12345
REDIRECT_URI = f"http://{REDIRECT_HOST}:{REDIRECT_PORT}/callback"


@dataclass
class OAuthCredentials:
    client_id: str
    client_secret: str


def get_oauth_credentials(config: dict | None = None) -> OAuthCredentials | None:
    """Get OAuth client credentials from environment or config.

    Priority: environment variables > config file.
    """
    client_id = os.environ.get("BUNQ_OAUTH_CLIENT_ID")
    client_secret = os.environ.get("BUNQ_OAUTH_CLIENT_SECRET")
    if client_id and client_secret:
        return OAuthCredentials(client_id=client_id, client_secret=client_secret)

    if config:
        oauth = config.get("oauth", {})
        client_id = oauth.get("client_id")
        client_secret = oauth.get("client_secret")
        if client_id and client_secret:
            return OAuthCredentials(client_id=client_id, client_secret=client_secret)

    return None


def oauth_login(sandbox: bool = False, config: dict | None = None) -> str:
    """Run the full OAuth browser flow and return an API token.

    Raises click.ClickException on failure.
    """
    creds = get_oauth_credentials(config)
    if creds is None:
        raise click.ClickException(
            "OAuth client not configured.\n"
            "Run 'bunq oauth-client register' first,\n"
            "or use 'bunq login --token YOUR_API_KEY' for direct API key authentication."
        )

    state = secrets.token_urlsafe(32)
    auth_code: str | None = None
    error: str | None = None
    server_ready = threading.Event()

    class CallbackHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            nonlocal auth_code, error
            parsed = urllib.parse.urlparse(self.path)
            params = urllib.parse.parse_qs(parsed.query)

            if parsed.path != "/callback":
                self.send_response(404)
                self.end_headers()
                return

            received_state = params.get("state", [None])[0]
            if received_state != state:
                error = "State mismatch -- possible CSRF attack."
                self._respond("Authorization failed: state mismatch.")
                return

            if "error" in params:
                error = params["error"][0]
                desc = params.get("error_description", [""])[0]
                self._respond(f"Authorization failed: {error}. {desc}")
                return

            code = params.get("code", [None])[0]
            if code is None:
                error = "No authorization code received."
                self._respond("Authorization failed: no code received.")
                return

            auth_code = code
            self._respond(
                "Authorization successful! You can close this tab and return to your terminal."
            )

        def _respond(self, message: str) -> None:
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            body = (
                "<!DOCTYPE html><html><head>"
                "<meta charset='utf-8'>"
                "<style>body{font-family:system-ui;max-width:480px;margin:80px auto;text-align:center}</style>"
                "</head><body>"
                f"<h2>{message}</h2>"
                "</body></html>"
            )
            self.wfile.write(body.encode())

        def log_message(self, format: str, *args: object) -> None:
            pass  # suppress request logs

    server = http.server.HTTPServer((REDIRECT_HOST, REDIRECT_PORT), CallbackHandler)

    def run_server() -> None:
        server_ready.set()
        server.handle_request()  # handle exactly one request

    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    server_ready.wait()

    # Build authorization URL
    auth_base = AUTH_URL_SANDBOX if sandbox else AUTH_URL_PRODUCTION
    auth_params = urllib.parse.urlencode({
        "response_type": "code",
        "client_id": creds.client_id,
        "redirect_uri": REDIRECT_URI,
        "state": state,
    })
    auth_url = f"{auth_base}?{auth_params}"

    click.echo(f"Opening browser for authorization...")
    click.echo(f"If the browser doesn't open, visit: {auth_url}")
    webbrowser.open(auth_url)

    # Wait for the callback
    thread.join(timeout=300)  # 5 minute timeout
    server.server_close()

    if auth_code is None:
        raise click.ClickException(error or "Authorization timed out.")

    # Exchange authorization code for access token
    token_url = TOKEN_URL_SANDBOX if sandbox else TOKEN_URL_PRODUCTION
    token_params = {
        "grant_type": "authorization_code",
        "code": auth_code,
        "redirect_uri": REDIRECT_URI,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
    }

    response = requests.post(token_url, params=token_params)
    if response.status_code != 200:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise click.ClickException(f"Token exchange failed ({response.status_code}): {detail}")

    data = response.json()
    access_token = data.get("access_token")
    if not access_token:
        raise click.ClickException(f"No access token in response: {data}")

    return access_token
