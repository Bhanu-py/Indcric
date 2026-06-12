"""Enable Banking AISP client — implements the AISPClient protocol from base.py.

Endpoints used:
- POST /auth                              — start consent flow (returns redirect URL)
- POST /sessions                          — exchange post-redirect code for accounts
- GET  /sessions/{id}                     — re-fetch session/accounts later
- GET  /aspsps?country=BE                 — list supported banks
- GET  /accounts/{id}/details             — account metadata
- GET  /accounts/{id}/transactions        — paginated booked transactions

Auth: RS256 JWT signed with our app's private key, kid = ENABLE_BANKING_APP_ID,
iss=enablebanking.com, aud=api.enablebanking.com, exp <= 24h from iat. Tokens
are minted per request with a 5-minute lifetime — well under Enable Banking's
ceiling, and short enough to limit replay if a token ever leaks in logs.
"""

from __future__ import annotations

import time
from datetime import date, datetime, timedelta, timezone as tz
from decimal import Decimal, InvalidOperation
from typing import Iterable

import jwt  # PyJWT[crypto]
import requests
from django.conf import settings

from .base import Transaction


API_BASE = "https://api.enablebanking.com"
_TOKEN_LIFETIME_SECONDS = 300
_TIMEOUT_SECONDS = 15


class EnableBankingError(Exception):
    """HTTP-level failure talking to Enable Banking. Wraps status + body so the
    caller (views, management commands) can render a useful message."""

    def __init__(self, status: int, body: str):
        super().__init__(f"HTTP {status}: {body}")
        self.status = status
        self.body = body


def _build_jwt() -> str:
    if not settings.ENABLE_BANKING_APP_ID:
        raise RuntimeError(
            "ENABLE_BANKING_APP_ID is not set. Add it to .env from the dashboard "
            "at https://enablebanking.com/cp/applications."
        )
    if not settings.ENABLE_BANKING_PRIVATE_KEY_PATH:
        raise RuntimeError(
            "ENABLE_BANKING_PRIVATE_KEY_PATH is not set. Point it at the .pem file "
            "you downloaded when registering the application."
        )
    with open(settings.ENABLE_BANKING_PRIVATE_KEY_PATH, 'rb') as f:
        private_key = f.read()
    now = int(time.time())
    return jwt.encode(
        {
            'iss': 'enablebanking.com',
            'aud': 'api.enablebanking.com',
            'iat': now,
            'exp': now + _TOKEN_LIFETIME_SECONDS,
        },
        private_key,
        algorithm='RS256',
        headers={'typ': 'JWT', 'kid': settings.ENABLE_BANKING_APP_ID},
    )


def _request(method: str, path: str, **kwargs) -> dict:
    headers = kwargs.pop('headers', {})
    headers['Authorization'] = f'Bearer {_build_jwt()}'
    headers.setdefault('Accept', 'application/json')
    resp = requests.request(
        method, f"{API_BASE}{path}",
        headers=headers, timeout=_TIMEOUT_SECONDS, **kwargs,
    )
    if not resp.ok:
        raise EnableBankingError(resp.status_code, resp.text[:500])
    return resp.json() if resp.content else {}


def list_aspsps(country: str = 'BE') -> list[dict]:
    """List banks supported in this country. Sandbox apps see only the Mock ASPSPs."""
    return _request('GET', '/aspsps', params={'country': country}).get('aspsps', [])


def start_session(
    *, aspsp_name: str, country: str, redirect_url: str, state: str,
    psu_type: str = 'personal', valid_until_days: int = 90,
) -> dict:
    """Begin consent. Returns {'url': str, 'authorization_id': str, ...}.

    Caller redirects the user's browser to `url`; the user authenticates with
    their bank, gets bounced back to `redirect_url` with `?code=...&state=...`.
    `state` is our CSRF token — store it in the session, verify on callback.
    """
    valid_until = datetime.now(tz.utc) + timedelta(days=valid_until_days)
    body = {
        'access': {
            'valid_until': valid_until.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
        },
        'aspsp': {'name': aspsp_name, 'country': country},
        'state': state,
        'redirect_url': redirect_url,
        'psu_type': psu_type,
    }
    return _request('POST', '/auth', json=body)


def complete_session(code: str) -> dict:
    """Exchange the post-redirect code for a session + the user's accounts.

    Returns {'session_id': str, 'accounts': [{'uid': str, 'iban': str, ...}], ...}.
    """
    return _request('POST', '/sessions', json={'code': code})


def get_session(session_id: str) -> dict:
    return _request('GET', f'/sessions/{session_id}')


def get_account_details(account_id: str) -> dict:
    return _request('GET', f'/accounts/{account_id}/details')


def get_transactions(
    *, account_id: str, date_from: date | None = None,
    transaction_status: str = 'BOOK',
) -> Iterable[Transaction]:
    """Yield normalised Transaction objects. Follows continuation_key pagination.

    transaction_status defaults to 'BOOK' (booked only — what we want for
    accounting). 'PDNG' = pending, which we deliberately skip: a pending
    SEPA transfer can be rejected at settlement, and we'd then have a fake
    Donation row to clean up.
    """
    params = {'transaction_status': transaction_status}
    if date_from is not None:
        params['date_from'] = date_from.isoformat()

    while True:
        resp = _request('GET', f'/accounts/{account_id}/transactions', params=params)
        for raw in resp.get('transactions', []):
            yield _normalize(raw)
        cont = resp.get('continuation_key')
        if not cont:
            return
        # Subsequent pages: send only the continuation key — the API echoes
        # the original filter set against it.
        params = {'continuation_key': cont}


def _normalize(raw: dict) -> Transaction:
    """Translate Enable Banking's transaction shape into our Transaction dataclass.

    Enable Banking returns:
      - transaction_id (or entry_reference as fallback)
      - booking_date / value_date  (YYYY-MM-DD)
      - transaction_amount: {amount, currency}     — magnitude only, unsigned
      - credit_debit_indicator: 'CRDT' (incoming) | 'DBIT' (outgoing)
      - debtor / debtor_account                    — sender side
      - creditor / creditor_account                — recipient side
      - remittance_information: [str]              — free-text reference lines

    We sign the amount ourselves: positive for credits, negative for debits.
    For incoming credits the counterparty is the debtor; the inverse for debits.
    """
    indicator = raw.get('credit_debit_indicator', 'CRDT')
    try:
        magnitude = Decimal(str(raw.get('transaction_amount', {}).get('amount', '0')))
    except (InvalidOperation, TypeError):
        magnitude = Decimal('0')
    amount = magnitude if indicator == 'CRDT' else -magnitude
    currency = (raw.get('transaction_amount') or {}).get('currency', 'EUR')

    if indicator == 'CRDT':
        party = raw.get('debtor') or {}
        party_account = raw.get('debtor_account') or {}
    else:
        party = raw.get('creditor') or {}
        party_account = raw.get('creditor_account') or {}

    name = party.get('name', '') if isinstance(party, dict) else ''
    iban = party_account.get('iban', '') if isinstance(party_account, dict) else ''

    remittance_lines = raw.get('remittance_information') or []
    remittance = ' '.join(s for s in remittance_lines if isinstance(s, str))

    booked_raw = raw.get('booking_date') or raw.get('value_date')
    value_raw = raw.get('value_date')

    return Transaction(
        transaction_id=raw.get('transaction_id') or raw.get('entry_reference') or '',
        booked_on=_parse_date(booked_raw) or date.today(),
        value_on=_parse_date(value_raw),
        amount=amount,
        currency=currency,
        counterparty_name=name,
        counterparty_iban=iban,
        remittance=remittance,
        raw=raw,
    )


def _parse_date(value) -> date | None:
    if not value:
        return None
    try:
        return date.fromisoformat(value)
    except (ValueError, TypeError):
        return None
