"""Provider-agnostic interface for any AISP (Account Information Service Provider).

The downstream import code (classification, Donation creation, review UI) talks
to this interface, not to Enable Banking specifically. Swapping providers later
(or running CSV upload alongside) is a matter of dropping in a new implementation.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Iterable, Protocol


@dataclass
class Transaction:
    """Normalised transaction shape. Each provider implementation translates its
    own response into this dataclass before handing it to the import pipeline."""
    transaction_id: str
    booked_on: date
    amount: Decimal
    currency: str
    counterparty_name: str = ''
    counterparty_iban: str = ''
    remittance: str = ''
    value_on: date | None = None
    raw: dict | None = None


class AISPClient(Protocol):
    """Minimum surface every bank-data provider must implement."""

    def start_session(
        self, *, aspsp: str, country: str, redirect_url: str, psu_type: str = 'personal',
    ) -> dict:
        """Initiate consent. Returns {'authorization_url': str, 'session_id': str}.
        The caller redirects the user's browser to authorization_url."""
        ...

    def complete_session(self, *, session_id: str, code: str) -> dict:
        """Exchange the post-redirect code for account access. Returns:
        {'session_id': str, 'accounts': [{'id': str, 'iban': str, ...}],
         'consent_valid_until': datetime}."""
        ...

    def get_transactions(
        self, *, account_id: str, date_from: date,
    ) -> Iterable[Transaction]:
        """Fetch booked transactions on or after date_from. Implementations
        should yield normalised Transaction objects, not raw API payloads."""
        ...
