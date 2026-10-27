# Cards

Bunq issues debit cards (Maestro and Mastercard) that are linked to your monetary accounts. The CLI lets you view and manage your cards.

## Listing cards

```bash
bunq cards list
```

## Viewing a card

```bash
bunq cards get 12345
```

This shows the card type, status, linked accounts, spending limits, and card settings.

## Updating card settings

### Freeze and unfreeze

Temporarily disable a card without cancelling it:

```bash
bunq cards freeze 12345
bunq cards unfreeze 12345
```

### Spending limits

Update the daily spending and ATM limits:

```bash
bunq cards update 12345 --daily-limit 500.00
bunq cards update 12345 --atm-limit 250.00
```

### PIN code

```bash
bunq cards update 12345 --change-pin
```

You'll be prompted for the new PIN, so it doesn't end up in your shell history.

### Linked accounts

Change which account a card draws from:

```bash
bunq cards update 12345 --account 67890
```

### Country permissions

Restrict where a card can be used:

```bash
# Allow only domestic transactions
bunq cards update 12345 --country-permission NL

# Allow multiple countries
bunq cards update 12345 --country-permission NL --country-permission DE --country-permission BE
```
