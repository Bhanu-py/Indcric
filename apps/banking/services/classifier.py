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

# Substring match, case-insensitive. Earlier we used \bicg\b to avoid false
# positives like 'ricgardo', but real-world bank references mash punctuation
# and tokens together in unpredictable ways ('ICGdonation', 'Donation/ICG2026',
# 'icg.bhanu') that word boundaries reject. Casting a wide net here and
# leaving false positives recoverable via the admin review step.
ICG_PATTERN = re.compile(r'icg', re.IGNORECASE)


def classify(txn: Transaction) -> str:
    """Return one of BankTransaction.STATUS_* given a normalised transaction.

    Rules:
    - Outgoing or zero amount  -> IGNORED
    - No 'icg' substring in remittance (any case)  -> IGNORED
    - 'icg' substring + positive credit  -> MATCHED  (caller may downgrade to
      REVIEW if there is no active campaign to attach the Donation to)
    """
    if txn.amount is None or txn.amount <= Decimal('0'):
        return BankTransaction.STATUS_IGNORED
    if not ICG_PATTERN.search(txn.remittance or ''):
        return BankTransaction.STATUS_IGNORED
    return BankTransaction.STATUS_MATCHED
