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
| `MUTATION` | Payments, transfers, and other balance changes |
| `PAYMENT` | Incoming and outgoing payments |
| `REQUEST` | Payment request updates |
| `CARD_TRANSACTION_SUCCESSFUL` | Successful card transactions |
| `CARD_TRANSACTION_FAILED` | Declined card transactions |
| `SCHEDULE_STATUS` | Scheduled payment status changes |
| `BUNQME_TAB` | bunq.me request updates |

Subscribe to multiple categories:

```bash
bunq callbacks create \
  --url "https://example.com/webhooks/bunq" \
  --category MUTATION \
  --category CARD_TRANSACTION_SUCCESSFUL
```

## Deleting a callback

```bash
bunq callbacks delete 12345
```
