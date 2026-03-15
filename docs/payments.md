# Payments

Payments are the core of Bunq -- sending and receiving money. The CLI supports listing transactions, creating payments, and managing drafts.

## Listing payments

```bash
# Payments on your default account
bunq payments list

# Payments on a specific account
bunq payments list --account 12345

# All payments (paginate automatically)
bunq payments list --all
```

## Viewing a payment

```bash
bunq payments get 12345 --account 67890
```

## Creating a payment

Send money to an IBAN:

```bash
bunq payments create \
  --account 12345 \
  --amount 25.00 \
  --currency EUR \
  --recipient-iban NL02ABNA0123456789 \
  --recipient-name "Jan de Vries" \
  --description "Dinner last Friday"
```

The `--currency` defaults to EUR if not specified.

## Draft payments

Draft payments require approval (e.g., from a second account holder on a joint account) before they are executed:

```bash
# Create a draft
bunq draft-payments create \
  --account 12345 \
  --amount 500.00 \
  --recipient-iban NL02ABNA0123456789 \
  --recipient-name "Acme Corp" \
  --description "Invoice 2024-001"

# List pending drafts
bunq draft-payments list --account 12345

# View a draft
bunq draft-payments get 67890 --account 12345
```

## Scheduled payments

Schedule a payment for a future date:

```bash
bunq scheduled-payments create \
  --account 12345 \
  --amount 750.00 \
  --recipient-iban NL02ABNA0123456789 \
  --recipient-name "Landlord B.V." \
  --description "Rent April" \
  --schedule-date 2024-04-01

# Recurring schedule
bunq scheduled-payments create \
  --account 12345 \
  --amount 750.00 \
  --recipient-iban NL02ABNA0123456789 \
  --recipient-name "Landlord B.V." \
  --description "Monthly rent" \
  --schedule-date 2024-04-01 \
  --frequency MONTHLY \
  --end-date 2025-03-01
```

**Frequencies:** `ONCE`, `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`.

```bash
# List scheduled payments
bunq scheduled-payments list --account 12345

# Cancel a scheduled payment
bunq scheduled-payments delete 67890 --account 12345
```

## International transfers

Bunq supports international transfers via TransferWise (Wise):

```bash
# Check available currencies
bunq transfers currencies

# Get a quote
bunq transfers quote \
  --amount 1000.00 \
  --currency-from EUR \
  --currency-to GBP

# Create a transfer
bunq transfers create \
  --account 12345 \
  --amount 1000.00 \
  --currency-from EUR \
  --currency-to GBP \
  --recipient-name "John Smith" \
  --recipient-iban GB29NWBK60161331926819
```
