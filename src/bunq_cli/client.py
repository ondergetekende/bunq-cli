"""Bunq API client wrapping the official SDK."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import click
from bunq.sdk.context.api_context import ApiContext
from bunq.sdk.context.api_environment_type import ApiEnvironmentType
from bunq.sdk.context.bunq_context import BunqContext
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

from bunq_cli.config import DEFAULT_CONTEXT_PATH

logger = logging.getLogger(__name__)

DEVICE_DESCRIPTION = "bunq-cli"


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
        api_context.save(path)

    BunqContext.load_api_context(api_context)


def create_context(
    api_key: str,
    context_path: Path | None = None,
    sandbox: bool = False,
) -> None:
    """Create a new API context (device registration + session)."""
    path = str(context_path or DEFAULT_CONTEXT_PATH)
    env = ApiEnvironmentType.SANDBOX if sandbox else ApiEnvironmentType.PRODUCTION
    api_context = ApiContext.create(env, api_key, DEVICE_DESCRIPTION)
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
        ):
            obj = getattr(account, attr, None)
            if obj is not None:
                iban = ""
                if obj.alias_:
                    for alias in obj.alias_:
                        if alias.type_ == "IBAN":
                            iban = alias.value
                            break
                return {
                    "id": obj.id_,
                    "description": obj.description,
                    "type": attr.replace("MonetaryAccount", ""),
                    "currency": obj.currency,
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
            "counterparty": (
                payment.counterparty_alias.display_name
                if payment.counterparty_alias
                else None
            ),
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
            "counterparty": (
                req.counterparty_alias.display_name
                if req.counterparty_alias
                else None
            ),
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
            "counterparty": (
                req.counterparty_alias.display_name
                if req.counterparty_alias
                else None
            ),
            "description": req.description,
            "status": req.status,
        }

    # -- Cards --

    def list_cards(self) -> list[dict]:
        """List all cards."""
        self._log("GET card (list)")
        pagination = Pagination()
        pagination.count = 100
        response = CardApiObject.list(params=pagination.url_params_count_only)
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
        }

    # -- Callbacks (notification filters) --

    def list_callbacks(self) -> list[dict]:
        """List notification filters."""
        self._log("GET notification-filter-url (list)")
        response = NotificationFilterUrlApiObject.list()
        return [self._callback_to_dict(f) for f in response.value]

    def create_callback(self, url: str, categories: list[str]) -> list[dict]:
        """Create notification filters for the given categories."""
        self._log(f"POST notification-filter-url categories={categories}")
        filters = [
            NotificationFilterUrlObject(category, url) for category in categories
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
            "id": f.id_ if hasattr(f, "id_") else None,
            "category": f.category,
            "notification_target": f.notification_target,
        }
