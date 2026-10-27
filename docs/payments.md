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

# Withdraw a pending draft
bunq draft-payments reject 67890 --account 12345
```

Drafts are approved in the bunq app.

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

**Frequencies:** `ONCE` (default), `HOURLY`, `DAILY`, `WEEKLY`, `MONTHLY`, `YEARLY`. Use `--every N` to repeat every N periods (e.g. `--frequency WEEKLY --every 2`). Dates are in local time; add a time with `--schedule-date "2024-04-01 09:00"`.

```bash
# List scheduled payments
bunq scheduled-payments list --account 12345

# Cancel a scheduled payment
bunq scheduled-payments delete 67890 --account 12345
```

## bunq.me payment links

Create a link anyone can pay with iDEAL, card or bunq:

```bash
bunq bunqme create --amount 15.00 --description "Concert tickets"
bunq bunqme list
bunq bunqme get 67890
bunq bunqme cancel 67890
```

## Card transactions

Card payments also show up in `bunq payments list`. For card-specific details (merchant, city, authorisation decision):

```bash
bunq cards transactions --account 12345
bunq cards transaction 67890 --account 12345
```

## Activity feed

Events cover everything that happens on your accounts (payments, requests, card transactions, schedule runs, ...):

```bash
bunq events list
bunq events list --account 12345 --count 50
bunq events get 67890
```

## Statements

Export a statement as CSV, PDF or MT940:

```bash
bunq statements create --from 2024-01-01 --to 2024-03-31 --format CSV
bunq statements list
bunq statements download 67890 -o q1.csv
bunq statements delete 67890
```

CSV statements use `;` separators by default; pass `--regional-format UK_US` for `,`.

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
