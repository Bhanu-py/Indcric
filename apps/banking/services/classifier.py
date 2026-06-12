"""Decide whether a fetched bank transaction is an ICG donation candidate.

This file deliberately has no provider import — it works on normalised
Transaction dataclasses, so the same logic applies to Enable Banking,
CSV upload, or any future intake.
"""

from __future__ import annotations

import re
from decimal import Decimal

from ..models import BankTransaction
from .base import Transaction

# \b on each side so "ICG donation - John" matches but "ricgardo" doesn't.
# Case-insensitive so "icg", "Icg", "ICG" all qualify.
ICG_PATTERN = re.compile(r'\bicg\b', re.IGNORECASE)


def classify(txn: Transaction) -> str:
    """Return one of BankTransaction.STATUS_* given a normalised transaction.

    Rules (intentionally narrow — false positives put a stranger's name on the
    public donor wall):
    - Outgoing or zero amount  -> IGNORED
    - No 'ICG' in remittance   -> IGNORED
    - 'ICG' + positive credit  -> MATCHED  (caller may downgrade to REVIEW if
       there is no active campaign to attach the Donation to)
    """
    if txn.amount is None or txn.amount <= Decimal('0'):
        return BankTransaction.STATUS_IGNORED
    if not ICG_PATTERN.search(txn.remittance or ''):
        return BankTransaction.STATUS_IGNORED
    return BankTransaction.STATUS_MATCHED
