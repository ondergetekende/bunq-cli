"""Bunq API client wrapping the official SDK."""

from __future__ import annotations

import json
import logging
import uuid
from pathlib import Path
from typing import Any

import click
import requests
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.api_environment_type import ApiEnvironmentType
from bunq.sdk.context.bunq_context import BunqContext
from bunq.sdk.http.api_client import ApiClient
from bunq.sdk.http.bunq_response_raw import BunqResponseRaw
from bunq.sdk.http.pagination import Pagination
from bunq.sdk.model.generated.endpoint import (
    CardApiObject,
    MonetaryAccountApiObject,
    NotificationFilterUrlApiObject,
    PaymentApiObject,
    RequestInquiryApiObject,
    RequestResponseApiObject,
)
from bunq.sdk.model.generated.object_ import (
    AmountObject,
    NotificationFilterUrlObject,
    PointerObject,
)

from bunq_cli.config import DEFAULT_CONTEXT_PATH, restrict_permissions

logger = logging.getLogger(__name__)

DEVICE_DESCRIPTION = "bunq-cli"
SANDBOX_USER_URL = "https://public-api.sandbox.bunq.com/v1/sandbox-user-person"


def _list_cards(params: dict[str, str]) -> Any:
    """Like CardApiObject.list, but accepts CardDebit/CardCredit/... list items.

    The SDK's list parser only accepts items wrapped as "Card".
    """
    api_client = ApiClient(CardApiObject._get_api_context())
    url = CardApiObject._ENDPOINT_URL_LISTING.format(CardApiObject._determine_user_id())
    raw = api_client.get(url, params, {})
    body = json.loads(raw.body_bytes)
    body["Response"] = [
        {"Card": next(v for k, v in item.items() if k.startswith("Card"))}
        for item in body["Response"]
    ]
    fixed = BunqResponseRaw(json.dumps(body).encode(), raw.headers)
    return CardApiObject._from_json_list(fixed, "Card")


def _counterparty_name(ref: Any) -> str | None:
    label = ref.label_monetary_account if ref else None
    return label.display_name if label else None


class BunqApiError(click.ClickException):
    """API error with context."""

    def __init__(self, message: str) -> None:
        super().__init__(f"Bunq API error: {message}")


def _ensure_context(
    context_path: Path | None = None,
    sandbox: bool = False,
) -> None:
    """Load an existing API context, refreshing the session if needed."""
    path = str(context_path or DEFAULT_CONTEXT_PATH)
    try:
        api_context = ApiContext.restore(path)
    except Exception as exc:
        raise BunqApiError(
            f"Could not load API context from {path}. Run 'bunq login' first."
        ) from exc

    if api_context.ensure_session_active():
        restrict_permissions(Path(path))
        api_context.save(path)

    BunqContext.load_api_context(api_context)


def create_context(
    api_key: str,
    context_path: Path | None = None,
    sandbox: bool = False,
    permitted_ips: list[str] | None = None,
) -> None:
    """Create a new API context (device registration + session).

    bunq invalidates API keys not assigned to an IP within 4 hours; the
    device registration assigns them to ``permitted_ips`` (default ``*``).
    """
    path = str(context_path or DEFAULT_CONTEXT_PATH)
    env = ApiEnvironmentType.SANDBOX if sandbox else ApiEnvironmentType.PRODUCTION
    api_context = ApiContext.create(
        env, api_key, DEVICE_DESCRIPTION, all_permitted_ip=permitted_ips or ["*"]
    )
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    restrict_permissions(Path(path))
    api_context.save(path)
    BunqContext.load_api_context(api_context)


def destroy_context(context_path: Path | None = None) -> None:
    """Close the session and delete the context file."""
    path = Path(context_path or DEFAULT_CONTEXT_PATH)
    if path.exists():
        try:
            api_context = ApiContext.restore(str(path))
            api_context.close_session()
        except Exception:
            pass
        path.unlink(missing_ok=True)


def create_sandbox_user() -> str:
    """Create a sandbox test user and return its API key."""
    response = requests.post(
        SANDBOX_USER_URL,
        headers={
            "Content-Type": "application/json",
            "Cache-Control": "no-cache",
            "User-Agent": DEVICE_DESCRIPTION,
            "X-Bunq-Client-Request-Id": str(uuid.uuid4()),
            "X-Bunq-Language": "en_US",
            "X-Bunq-Region": "nl_NL",
            "X-Bunq-Geolocation": "0 0 0 0 000",
        },
        timeout=30,
    )
    if not response.ok:
        raise BunqApiError(f"Creating sandbox user failed ({response.status_code}): {response.text}")
    return response.json()["Response"][0]["ApiKey"]["api_key"]


def _amount(value: str, currency: str) -> dict:
    return {"value": value, "currency": currency}


def _iban(iban: str, name: str) -> dict:
    return {"type": "IBAN", "value": iban, "name": name}


def _name(label: dict | None) -> str | None:
    return (label or {}).get("display_name")


class BunqClient:
    """High-level client wrapping the bunq SDK for CLI use."""

    def __init__(
        self,
        context_path: Path | None = None,
        sandbox: bool = False,
        verbose: bool = False,
    ) -> None:
        self.verbose = verbose
        self.sandbox = sandbox
        _ensure_context(context_path, sandbox)

    def _log(self, message: str) -> None:
        if self.verbose:
            click.echo(message, err=True)

    # -- Raw API access (the SDK misparses or lacks fields for several endpoints) --

    @staticmethod
    def _user_path(path: str) -> str:
        return f"user/{BunqContext.user_context().user_id}/{path}"

    @classmethod
    def _account_path(cls, path: str, account_id: int | None) -> str:
        if account_id is None:
            account_id = BunqContext.user_context().primary_monetary_account.id_
        return cls._user_path(f"monetary-account/{account_id}/{path}")

    def _call(
        self,
        method: str,
        path: str,
        body: dict | None = None,
        params: dict[str, str] | None = None,
    ) -> list[dict]:
        """Call the API and return the unwrapped items of the "Response" array."""
        self._log(f"{method} {path}")
        api = ApiClient(BunqContext.api_context())
        if method == "GET":
            raw = api.get(path, params or {}, {})
        elif method == "DELETE":
            raw = api.delete(path, {})
        else:
            raw = getattr(api, method.lower())(path, json.dumps(body or {}).encode(), {})
        if not raw.body_bytes:
            return []
        response = json.loads(raw.body_bytes).get("Response", [])
        return [next(iter(item.values())) for item in response]

    def _create(self, path: str, body: dict) -> int:
        return self._call("POST", path, body)[0]["id"]

    @staticmethod
    def _page_params(count: int, older_id: int | None) -> dict[str, str]:
        params = {"count": str(count)}
        if older_id is not None:
            params["older_id"] = str(older_id)
        return params

    # -- Accounts --

    def list_accounts(self) -> list[dict]:
        """List all monetary accounts."""
        self._log("GET monetary-account (list)")
        pagination = Pagination()
        pagination.count = 100
        response = MonetaryAccountApiObject.list(
            params=pagination.url_params_count_only
        )
        return [self._account_to_dict(a) for a in response.value]

    def get_account(self, account_id: int) -> dict:
        """Get a single monetary account."""
        self._log(f"GET monetary-account/{account_id}")
        response = MonetaryAccountApiObject.get(account_id)
        return self._account_to_dict(response.value)

    @staticmethod
    def _account_to_dict(account: Any) -> dict:
        """Convert a MonetaryAccountApiObject to a flat dict."""
        # The SDK returns an anchor object; find the non-None sub-type
        for attr in (
            "MonetaryAccountBank",
            "MonetaryAccountSavings",
            "MonetaryAccountJoint",
            "MonetaryAccountLight",
            "MonetaryAccountExternal",
            "MonetaryAccountExternalSavings",
            "MonetaryAccountInvestment",
            "MonetaryAccountCard",
            "MonetaryAccountSwitchService",
        ):
            obj = getattr(account, attr, None)
            if obj is not None:
                iban = ""
                if obj.alias:
                    for alias in obj.alias:
                        if alias.type_ == "IBAN":
                            iban = alias.value
                            break
                return {
                    "id": obj.id_,
                    "description": obj.description,
                    "type": attr.replace("MonetaryAccount", ""),
                    "currency": getattr(obj, "currency", None)
                    or (obj.balance.currency if obj.balance else None),
                    "balance": obj.balance.value if obj.balance else None,
                    "iban": iban,
                    "status": obj.status,
                }
        return {"id": getattr(account, "id_", None)}

    # -- Payments --

    def list_payments(
        self,
        account_id: int | None = None,
        count: int = 25,
        older_id: int | None = None,
        newer_id: int | None = None,
    ) -> list[dict]:
        """List payments on an account."""
        self._log(f"GET payment (list) account={account_id}")
        pagination = Pagination()
        pagination.count = count
        if older_id is not None:
            pagination.older_id = older_id
        if newer_id is not None:
            pagination.newer_id = newer_id

        params = pagination.url_params_count_only
        if older_id is not None:
            params = pagination.url_params_previous_page
        elif newer_id is not None:
            params = pagination.url_params_next_page

        response = PaymentApiObject.list(
            monetary_account_id=account_id,
            params=params,
        )
        return [self._payment_to_dict(p) for p in response.value]

    def list_all_payments(self, account_id: int | None = None) -> list[dict]:
        """List all payments, handling pagination automatically."""
        self._log(f"GET payment (list all) account={account_id}")
        results: list[dict] = []
        pagination = Pagination()
        pagination.count = 100

        response = PaymentApiObject.list(
            monetary_account_id=account_id,
            params=pagination.url_params_count_only,
        )
        results.extend(self._payment_to_dict(p) for p in response.value)

        while response.pagination.has_previous_page():
            response = PaymentApiObject.list(
                monetary_account_id=account_id,
                params=response.pagination.url_params_previous_page,
            )
            results.extend(self._payment_to_dict(p) for p in response.value)

        return results

    def get_payment(self, payment_id: int, account_id: int | None = None) -> dict:
        """Get a single payment."""
        self._log(f"GET payment/{payment_id} account={account_id}")
        response = PaymentApiObject.get(
            payment_id, monetary_account_id=account_id
        )
        return self._payment_to_dict(response.value)

    def create_payment(
        self,
        amount: str,
        currency: str,
        recipient_iban: str,
        recipient_name: str,
        description: str,
        account_id: int | None = None,
    ) -> int:
        """Create a payment. Returns the payment ID."""
        self._log(f"POST payment account={account_id}")
        response = PaymentApiObject.create(
            amount=AmountObject(amount, currency),
            counterparty_alias=PointerObject("IBAN", recipient_iban, recipient_name),
            description=description,
            monetary_account_id=account_id,
        )
        return response.value

    @staticmethod
    def _payment_to_dict(payment: Any) -> dict:
        return {
            "id": payment.id_,
            "created": payment.created,
            "amount": payment.amount.value if payment.amount else None,
            "currency": payment.amount.currency if payment.amount else None,
            "counterparty": _counterparty_name(payment.counterparty_alias),
            "description": payment.description,
            "type": payment.type_,
            "balance_after": (
                payment.balance_after_mutation.value
                if payment.balance_after_mutation
                else None
            ),
        }

    # -- Request Inquiries (payment requests) --

    def list_requests(self, account_id: int | None = None) -> list[dict]:
        """List outgoing payment requests."""
        self._log(f"GET request-inquiry (list) account={account_id}")
        pagination = Pagination()
        pagination.count = 100
        response = RequestInquiryApiObject.list(
            monetary_account_id=account_id,
            params=pagination.url_params_count_only,
        )
        return [self._request_inquiry_to_dict(r) for r in response.value]

    def get_request(
        self, request_id: int, account_id: int | None = None
    ) -> dict:
        """Get a single outgoing payment request."""
        self._log(f"GET request-inquiry/{request_id} account={account_id}")
        response = RequestInquiryApiObject.get(
            request_id, monetary_account_id=account_id
        )
        return self._request_inquiry_to_dict(response.value)

    def create_request(
        self,
        amount: str,
        currency: str,
        counterparty_type: str,
        counterparty_value: str,
        description: str,
        account_id: int | None = None,
    ) -> int:
        """Create a payment request. Returns the request ID."""
        self._log(f"POST request-inquiry account={account_id}")
        response = RequestInquiryApiObject.create(
            amount_inquired=AmountObject(amount, currency),
            counterparty_alias=PointerObject(counterparty_type, counterparty_value),
            description=description,
            allow_bunqme=True,
            monetary_account_id=account_id,
        )
        return response.value

    def revoke_request(
        self, request_id: int, account_id: int | None = None
    ) -> None:
        """Revoke a pending payment request."""
        self._log(f"PUT request-inquiry/{request_id} (revoke)")
        RequestInquiryApiObject.update(
            request_id,
            status="REVOKED",
            monetary_account_id=account_id,
        )

    def list_incoming_requests(self, account_id: int | None = None) -> list[dict]:
        """List incoming payment requests."""
        self._log(f"GET request-response (list) account={account_id}")
        pagination = Pagination()
        pagination.count = 100
        response = RequestResponseApiObject.list(
            monetary_account_id=account_id,
            params=pagination.url_params_count_only,
        )
        return [self._request_response_to_dict(r) for r in response.value]

    def accept_request(
        self, request_id: int, account_id: int | None = None
    ) -> None:
        """Accept an incoming payment request."""
        self._log(f"PUT request-response/{request_id} (accept)")
        RequestResponseApiObject.update(
            request_id,
            status="ACCEPTED",
            monetary_account_id=account_id,
        )

    def reject_request(
        self, request_id: int, account_id: int | None = None
    ) -> None:
        """Reject an incoming payment request."""
        self._log(f"PUT request-response/{request_id} (reject)")
        RequestResponseApiObject.update(
            request_id,
            status="REJECTED",
            monetary_account_id=account_id,
        )

    @staticmethod
    def _request_inquiry_to_dict(req: Any) -> dict:
        return {
            "id": req.id_,
            "created": req.created,
            "updated": req.updated,
            "amount": req.amount_inquired.value if req.amount_inquired else None,
            "currency": req.amount_inquired.currency if req.amount_inquired else None,
            "counterparty": _counterparty_name(req.counterparty_alias),
            "description": req.description,
            "status": req.status,
        }

    @staticmethod
    def _request_response_to_dict(req: Any) -> dict:
        return {
            "id": req.id_,
            "created": req.created,
            "updated": req.updated,
            "amount": req.amount_inquired.value if req.amount_inquired else None,
            "currency": req.amount_inquired.currency if req.amount_inquired else None,
            "counterparty": _counterparty_name(req.counterparty_alias),
            "description": req.description,
            "status": req.status,
        }

    # -- Cards --

    def list_cards(self) -> list[dict]:
        """List all cards."""
        self._log("GET card (list)")
        pagination = Pagination()
        pagination.count = 100
        response = _list_cards(pagination.url_params_count_only)
        return [self._card_to_dict(c) for c in response.value]

    def get_card(self, card_id: int) -> dict:
        """Get a single card."""
        self._log(f"GET card/{card_id}")
        response = CardApiObject.get(card_id)
        return self._card_to_dict(response.value)

    def update_card(self, card_id: int, **kwargs: Any) -> dict:
        """Update card settings."""
        self._log(f"PUT card/{card_id}")
        CardApiObject.update(card_id, **kwargs)
        return self.get_card(card_id)

    @staticmethod
    def _card_to_dict(card: Any) -> dict:
        return {
            "id": card.id_,
            "type": card.type_,
            "product_type": card.product_type,
            "status": card.status,
            "second_line": card.second_line,
            "expiry_date": card.expiry_date,
            "card_limit": (
                card.card_limit.value if card.card_limit else None
            ),
            "card_limit_atm": (
                card.card_limit_atm.value if card.card_limit_atm else None
            ),
            "countries": ",".join(
                p.country for p in (card.country_permission or [])
            ),
        }

    # -- Card transactions (mastercard-action) --

    def list_card_transactions(
        self, account_id: int | None = None, count: int = 25, older_id: int | None = None
    ) -> list[dict]:
        path = self._account_path("mastercard-action", account_id)
        items = self._call("GET", path, params=self._page_params(count, older_id))
        return [self._card_transaction_to_dict(t) for t in items]

    def get_card_transaction(self, transaction_id: int, account_id: int | None = None) -> dict:
        path = self._account_path(f"mastercard-action/{transaction_id}", account_id)
        return self._card_transaction_to_dict(self._call("GET", path)[0])

    @staticmethod
    def _card_transaction_to_dict(t: dict) -> dict:
        amount = t.get("amount_billing") or {}
        return {
            "id": t.get("id"),
            "created": t.get("created"),
            "amount": amount.get("value"),
            "currency": amount.get("currency"),
            "merchant": _name(t.get("counterparty_alias")),
            "city": t.get("city"),
            "description": t.get("description"),
            "card_id": t.get("card_id"),
            "decision": t.get("decision"),
            "status": t.get("payment_status"),
        }

    # -- Events --

    def list_events(
        self, account_id: int | None = None, count: int = 25, older_id: int | None = None
    ) -> list[dict]:
        params = self._page_params(count, older_id)
        if account_id is not None:
            params["monetary_account_id"] = str(account_id)
        items = self._call("GET", self._user_path("event"), params=params)
        return [self._event_to_dict(e) for e in items]

    def get_event(self, event_id: int) -> dict:
        event = self._call("GET", self._user_path(f"event/{event_id}"))[0]
        return {**self._event_to_dict(event), "object": event.get("object")}

    @staticmethod
    def _event_to_dict(e: dict) -> dict:
        object_type, obj = next(iter((e.get("object") or {"": {}}).items()))
        return {
            "id": e.get("id"),
            "created": e.get("created"),
            "action": e.get("action"),
            "object_type": object_type,
            "object_id": (obj or {}).get("id"),
            "account_id": e.get("monetary_account_id"),
            "status": e.get("status"),
        }

    # -- Statements (customer-statement) --

    def list_statements(self, account_id: int | None = None) -> list[dict]:
        items = self._call("GET", self._account_path("customer-statement", account_id))
        return [self._statement_to_dict(s) for s in items]

    def create_statement(
        self,
        statement_format: str,
        date_start: str,
        date_end: str,
        regional_format: str | None = None,
        account_id: int | None = None,
    ) -> int:
        body = {
            "statement_format": statement_format,
            "date_start": date_start,
            "date_end": date_end,
        }
        if regional_format:
            body["regional_format"] = regional_format
        return self._create(self._account_path("customer-statement", account_id), body)

    def download_statement(self, statement_id: int, account_id: int | None = None) -> bytes:
        path = self._account_path(f"customer-statement/{statement_id}/content", account_id)
        self._log(f"GET {path}")
        return ApiClient(BunqContext.api_context()).get(path, {}, {}).body_bytes

    def delete_statement(self, statement_id: int, account_id: int | None = None) -> None:
        self._call("DELETE", self._account_path(f"customer-statement/{statement_id}", account_id))

    @staticmethod
    def _statement_to_dict(s: dict) -> dict:
        return {
            "id": s.get("id"),
            "created": s.get("created"),
            "date_start": s.get("date_start"),
            "date_end": s.get("date_end"),
            "format": s.get("statement_format"),
            "regional_format": s.get("regional_format"),
            "status": s.get("status"),
        }

    # -- Scheduled payments --

    def list_scheduled_payments(self, account_id: int | None = None) -> list[dict]:
        items = self._call("GET", self._account_path("schedule-payment", account_id))
        return [self._scheduled_payment_to_dict(s) for s in items]

    def get_scheduled_payment(self, schedule_id: int, account_id: int | None = None) -> dict:
        path = self._account_path(f"schedule-payment/{schedule_id}", account_id)
        return self._scheduled_payment_to_dict(self._call("GET", path)[0])

    def create_scheduled_payment(
        self,
        amount: str,
        currency: str,
        recipient_iban: str,
        recipient_name: str,
        description: str,
        time_start: str,
        recurrence_unit: str,
        recurrence_size: int,
        time_end: str | None = None,
        account_id: int | None = None,
    ) -> int:
        schedule = {
            "time_start": time_start,
            "recurrence_unit": recurrence_unit,
            "recurrence_size": recurrence_size,
        }
        if time_end:
            schedule["time_end"] = time_end
        body = {
            "payment": {
                "amount": _amount(amount, currency),
                "counterparty_alias": _iban(recipient_iban, recipient_name),
                "description": description,
            },
            "schedule": schedule,
        }
        return self._create(self._account_path("schedule-payment", account_id), body)

    def cancel_scheduled_payment(self, schedule_id: int, account_id: int | None = None) -> None:
        self._call("DELETE", self._account_path(f"schedule-payment/{schedule_id}", account_id))

    @staticmethod
    def _scheduled_payment_to_dict(s: dict) -> dict:
        payment = s.get("payment") or {}
        schedule = s.get("schedule") or {}
        amount = payment.get("amount") or {}
        return {
            "id": s.get("id"),
            "status": s.get("status"),
            "amount": amount.get("value"),
            "currency": amount.get("currency"),
            "counterparty": _name(payment.get("counterparty_alias")),
            "description": payment.get("description"),
            "every": f"{schedule.get('recurrence_size')} {schedule.get('recurrence_unit')}",
            "next": schedule.get("time_next"),
            "start": schedule.get("time_start"),
            "end": schedule.get("time_end"),
        }

    # -- Draft payments --

    def list_draft_payments(self, account_id: int | None = None) -> list[dict]:
        items = self._call("GET", self._account_path("draft-payment", account_id))
        return [self._draft_payment_to_dict(d) for d in items]

    def get_draft_payment(self, draft_id: int, account_id: int | None = None) -> dict:
        path = self._account_path(f"draft-payment/{draft_id}", account_id)
        return self._draft_payment_to_dict(self._call("GET", path)[0])

    def create_draft_payment(
        self,
        amount: str,
        currency: str,
        recipient_iban: str,
        recipient_name: str,
        description: str,
        account_id: int | None = None,
    ) -> int:
        body = {
            "entries": [
                {
                    "amount": _amount(amount, currency),
                    "counterparty_alias": _iban(recipient_iban, recipient_name),
                    "description": description,
                }
            ],
            "number_of_required_accepts": 1,
        }
        return self._create(self._account_path("draft-payment", account_id), body)

    def reject_draft_payment(self, draft_id: int, account_id: int | None = None) -> None:
        path = self._account_path(f"draft-payment/{draft_id}", account_id)
        updated = self._call("GET", path)[0]["updated"]
        self._call("PUT", path, {"status": "REJECTED", "previous_updated_timestamp": updated})

    @staticmethod
    def _draft_payment_to_dict(d: dict) -> dict:
        entries = d.get("entries") or [{}]
        amount = entries[0].get("amount") or {}
        return {
            "id": d.get("id"),
            "created": d.get("created"),
            "status": d.get("status"),
            "amount": amount.get("value"),
            "currency": amount.get("currency"),
            "counterparty": _name(entries[0].get("counterparty_alias")),
            "description": entries[0].get("description"),
            "entries": len(d.get("entries") or []),
        }

    # -- bunq.me tabs --

    def list_bunqme_tabs(self, account_id: int | None = None) -> list[dict]:
        items = self._call("GET", self._account_path("bunqme-tab", account_id))
        return [self._bunqme_tab_to_dict(t) for t in items]

    def get_bunqme_tab(self, tab_id: int, account_id: int | None = None) -> dict:
        path = self._account_path(f"bunqme-tab/{tab_id}", account_id)
        return self._bunqme_tab_to_dict(self._call("GET", path)[0])

    def create_bunqme_tab(
        self,
        amount: str,
        currency: str,
        description: str,
        redirect_url: str | None = None,
        account_id: int | None = None,
    ) -> dict:
        entry = {"amount_inquired": _amount(amount, currency), "description": description}
        if redirect_url:
            entry["redirect_url"] = redirect_url
        tab_id = self._create(
            self._account_path("bunqme-tab", account_id), {"bunqme_tab_entry": entry}
        )
        return self.get_bunqme_tab(tab_id, account_id)

    def cancel_bunqme_tab(self, tab_id: int, account_id: int | None = None) -> None:
        path = self._account_path(f"bunqme-tab/{tab_id}", account_id)
        self._call("PUT", path, {"status": "CANCELLED"})

    @staticmethod
    def _bunqme_tab_to_dict(t: dict) -> dict:
        entry = t.get("bunqme_tab_entry") or {}
        amount = entry.get("amount_inquired") or {}
        return {
            "id": t.get("id"),
            "created": t.get("created"),
            "status": t.get("status"),
            "amount": amount.get("value"),
            "currency": amount.get("currency"),
            "description": entry.get("description"),
            "url": t.get("bunqme_tab_share_url"),
            "expires": t.get("time_expiry"),
        }

    # -- Callbacks (notification filters) --

    def list_callbacks(self) -> list[dict]:
        """List notification filters."""
        self._log("GET notification-filter-url (list)")
        response = NotificationFilterUrlApiObject.list()
        return [
            self._callback_to_dict(f)
            for item in response.value
            for f in (item.notification_filters or [])
        ]

    def create_callback(self, url: str, categories: list[str]) -> list[dict]:
        """Add notification filters for the given categories."""
        self._log(f"POST notification-filter-url categories={categories}")
        # POST replaces the full set of filters, so keep the existing ones.
        filters = [
            NotificationFilterUrlObject(f["category"], f["notification_target"])
            for f in self.list_callbacks()
        ]
        existing = {(f.category, f.notification_target) for f in filters}
        filters += [
            NotificationFilterUrlObject(category, url)
            for category in categories
            if (category, url) not in existing
        ]
        NotificationFilterUrlApiObject.create(notification_filters=filters)
        return self.list_callbacks()

    def delete_all_callbacks(self) -> None:
        """Remove all notification filters."""
        self._log("DELETE notification-filter-url (all)")
        NotificationFilterUrlApiObject.create(notification_filters=[])

    @staticmethod
    def _callback_to_dict(f: Any) -> dict:
        return {
            "id": getattr(f, "id_", None),
            "category": f.category,
            "notification_target": f.notification_target,
        }

    def list_callback_failures(self) -> list[dict]:
        items = self._call("GET", self._user_path("notification-filter-failure"))
        return [
            {
                "id": f.get("id"),
                "created": f.get("created"),
                "category": f.get("category"),
                "event_type": f.get("event_type"),
                "object_id": f.get("object_id"),
                "response_code": f.get("response_code"),
                "error": f.get("exception_message"),
            }
            for f in items
        ]

    def retry_callback_failures(self, failure_ids: list[int]) -> None:
        body = {"notification_filter_failed_ids": ",".join(map(str, failure_ids))}
        self._call("POST", self._user_path("notification-filter-failure"), body)
