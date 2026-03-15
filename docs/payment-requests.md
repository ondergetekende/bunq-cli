# Payment Requests

Payment requests (called "Request Inquiries" in the Bunq API) let you request money from other people. The recipient receives a notification and can accept or reject the request.

## Creating a request

Request money from another Bunq user by email or phone:

```bash
bunq requests create \
  --account 12345 \
  --amount 35.00 \
  --currency EUR \
  --counterparty-email friend@example.com \
  --description "Concert tickets"
```

Or by phone number:

```bash
bunq requests create \
  --account 12345 \
  --amount 15.00 \
  --counterparty-phone "+31612345678" \
  --description "Lunch"
```

## Listing sent requests

```bash
# Requests you sent
bunq requests list --account 12345

# All pages
bunq requests list --account 12345 --all
```

## Viewing a request

```bash
bunq requests get 67890 --account 12345
```

The output shows the status: `PENDING`, `ACCEPTED`, `REJECTED`, `REVOKED`, or `EXPIRED`.

## Revoking a request

Cancel a pending request:

```bash
bunq requests revoke 67890 --account 12345
```

## Incoming requests

View payment requests others have sent to you:

```bash
# List incoming requests
bunq requests incoming --account 12345

# Accept a request
bunq requests accept 67890 --account 12345

# Reject a request
bunq requests reject 67890 --account 12345
```
