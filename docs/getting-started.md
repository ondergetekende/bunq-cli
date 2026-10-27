# Getting Started

## What is Bunq?

[Bunq](https://www.bunq.com/) is a Dutch online bank that offers personal and business accounts, cards, and payments. It provides a public API for building integrations.

This CLI lets you interact with your Bunq accounts from the terminal -- useful for scripting, automation, and quick lookups without opening the app.

## Installation

```bash
pip install bunq-cli
```

This installs a `bunq` command in your PATH.

## Authentication

### Step 1: Get an API key

You need an API key for initial setup. Open the Bunq app on your phone:

1. Go to **Profile** > **Security & Privacy** > **Developers** > **API keys**.
2. Create a new API key and copy it.

Log in with it:

```bash
bunq login --token YOUR_API_KEY
```

### Step 2: Register an OAuth client

Bunq doesn't have a web portal for OAuth client registration -- it's done via the API. The CLI handles this for you:

```bash
bunq oauth-client register
```

This creates an OAuth client, registers the local callback URL, and stores the `client_id` and `client_secret` in `~/.config/bunq-cli.toml`. You can inspect them with:

```bash
bunq oauth-client show
```

You only need to do this once. Each Bunq user can have one OAuth client.

### Step 3: Log in with OAuth

From now on, you can log in without an API key:

```bash
bunq login
```

This opens your browser, you approve access on Bunq's website, and the CLI receives a token automatically via a local server on `http://127.0.0.1:12345/callback`.

### API key (alternative)

If you prefer to skip OAuth entirely (e.g., for scripting or server environments where a browser isn't available), you can always use an API key directly:

```bash
bunq login --token YOUR_API_KEY
```

API keys are only permitted for private integrations that you control yourself.

### Environment variable override

If you want to override the stored OAuth credentials (e.g., for testing), set these environment variables:

```bash
export BUNQ_OAUTH_CLIENT_ID="your-client-id"
export BUNQ_OAUTH_CLIENT_SECRET="your-client-secret"
```

Environment variables take precedence over the config file.

### Logging out

```bash
bunq logout
```

This removes stored credentials from the config file.

## Sandbox mode

Bunq provides a sandbox environment for testing. To use it:

```bash
bunq login --sandbox
bunq login --token YOUR_SANDBOX_TOKEN --sandbox
```

Sandbox mode uses the `https://public-api.sandbox.bunq.com` endpoint instead of production.

Create a sandbox test user and log in with it in one go (this replaces your current login):

```bash
bunq sandbox create-user --login
```

Without `--login` the new user's API key is printed. To get sandbox money, request it from bunq's test account:

```bash
bunq requests create --counterparty-email sugardaddy@bunq.com --amount 500.00 --description "Sandbox money"
```

## Output formats

By default the CLI prints tables when you're in a terminal, and JSON when output is piped:

```bash
# Human-readable table
bunq accounts list

# JSON for scripting
bunq accounts list | jq '.[].description'

# Force a format
bunq accounts list --output json
bunq accounts list --output table
```

## Pagination

All `list` commands return the first page of results by default. To fetch everything:

```bash
bunq payments list --all
```

Or navigate manually:

```bash
bunq payments list --count 50 --older-id 12345
bunq payments list --newer-id 67890
```

The `--all` flag handles Bunq's cursor-based pagination automatically.

## Global options

These can be used with any command:

| Option | Description |
|---|---|
| `--help` | Show help for a command |
| `--version` | Show version |
| `-v, --verbose` | Print HTTP requests to stderr |
| `-q, --quiet` | Suppress non-error output |
| `--token TOKEN` | Override the stored API token |
| `--output auto\|json\|table` | Force output format |
| `--no-color` | Disable colored output |
| `--config PATH` | Use a custom config file |
| `--sandbox` | Use the sandbox environment |
