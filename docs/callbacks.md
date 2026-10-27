# Callbacks

Callbacks (notification filters) let you receive real-time HTTP notifications when events happen on your Bunq account -- for example, when a payment is received or a card transaction occurs. This is useful for integrating Bunq with other systems.

## Listing callbacks

```bash
bunq callbacks list
```

## Creating a callback

```bash
bunq callbacks create \
  --url "https://example.com/webhooks/bunq" \
  --category MUTATION
```

**Categories:**

| Category | Events |
|---|---|
| `MUTATION` | Any balance change (payments, requests, iDEAL, etc.) |
| `PAYMENT` | Incoming and outgoing payments |
| `INSTANT_PAYMENT` | Instant (SCT Inst) payments |
| `REQUEST` | Payment request updates |
| `CARD_TRANSACTION_SUCCESSFUL` | Successful card transactions |
| `CARD_TRANSACTION_FAILED` | Declined card transactions |
| `SCHEDULE_STATUS` | Scheduled payment status changes |
| `BUNQME_TAB` | bunq.me request updates |
| `OAUTH` | OAuth connection revoked |

Run `bunq callbacks create --help` for the full list. The URL must use HTTPS. New filters are added to the existing ones.

Subscribe to multiple categories:

```bash
bunq callbacks create \
  --url "https://example.com/webhooks/bunq" \
  --category MUTATION \
  --category CARD_TRANSACTION_SUCCESSFUL
```

## Deleting callbacks

Removes all notification filters:

```bash
bunq callbacks delete
```

## Failed callbacks

bunq retries a failed callback 5 times, one minute apart. After that it is stored as a failure, which you can list and retry:

```bash
bunq callbacks failures
bunq callbacks retry 101 102 103
```
