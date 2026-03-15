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

The recommended way to log in is via OAuth. The CLI opens your browser, you approve access on Bunq's website, and the CLI receives a token automatically:

```bash
bunq login
```

This starts a temporary local server, opens the Bunq authorization page in your browser, and stores the resulting credentials in `~/.config/bunq-cli.toml`.

### API key (alternative)

If you prefer to use an API key directly (e.g., for scripting or server environments where a browser isn't available):

1. Open the Bunq app on your phone.
2. Go to **Profile** > **Security & Privacy** > **Developers** > **API keys**.
3. Create a new API key and reveal it.

```bash
bunq login --token YOUR_API_TOKEN
```

API keys are only permitted for private integrations that you control yourself. If you're building a tool for others to use, you must use OAuth.

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
