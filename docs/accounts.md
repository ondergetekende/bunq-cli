# Accounts

Monetary accounts in Bunq are your bank accounts -- current accounts, savings accounts, and joint accounts. Every payment and card is tied to a monetary account.

## Listing accounts

```bash
# All active accounts
bunq accounts list

# Include closed accounts
bunq accounts list --include-inactive
```

## Viewing an account

```bash
bunq accounts get 12345
```

This shows the full account details including IBAN, balance, and settings.

## Account types

Bunq offers several account types. The CLI displays the type in list output:

- **MonetaryAccountBank** -- standard current accounts
- **MonetaryAccountSavings** -- savings accounts
- **MonetaryAccountJoint** -- shared accounts with another Bunq user

## Checking your balance

```bash
# Quick overview of all balances
bunq accounts list --output table
```

The table output includes the account description, IBAN, and current balance.
