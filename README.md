# Bunq CLI

A command-line interface for [Bunq](https://www.bunq.com/), the online bank. Manage accounts, payments, cards, and more from your terminal.

> **Disclaimer:** This project is not affiliated with, endorsed by, or in any way associated with Bunq B.V. "Bunq" is a trademark of Bunq N.V. This is an independent, open-source tool that uses the public Bunq API.

## Quick start

```bash
pip install bunq-cli
bunq login
bunq accounts list
bunq payments list --account "My Account"
```

See [Getting Started](docs/getting-started.md) for full setup instructions, output formats, pagination, and global options.

## Documentation

| Guide | What it covers |
| --- | --- |
| [Getting Started](docs/getting-started.md) | Installation, authentication, profiles (multiple clients), sandbox mode, output formats, pagination, global options |
| [Accounts](docs/accounts.md) | Monetary accounts: list, get, create savings goals |
| [Payments](docs/payments.md) | Payments, drafts, scheduled payments, batch payments, international transfers |
| [Payment Requests](docs/payment-requests.md) | Request money from others, manage incoming requests |
| [Cards](docs/cards.md) | Card management: list, get, update settings, freeze/unfreeze |
| [Callbacks](docs/callbacks.md) | Notification filters and webhook management |

## Tech stack

- [Python](https://www.python.org/) >= 3.11
- [Click](https://click.palletsprojects.com/) for the CLI framework
- [bunq SDK](https://github.com/bunq/sdk_python) for the Bunq API
- [Tabulate](https://pypi.org/project/tabulate/) for table formatting

## License

MIT -- see [LICENSE](LICENSE).
