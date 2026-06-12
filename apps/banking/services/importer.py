"""Bank-transaction import pipeline.

One entry point — `import_all_links()` — used by both the management command
and (later) the cron-callable endpoint. Idempotent: the provider's stable
`transaction_id` is the dedupe key, so re-running this against the same window
is safe and cheap.

Flow per link:
  1. Skip if consent has expired; warn if < 14 days left.
  2. Fetch booked transactions since `last_synced_at - 3 days` (overlap catches
     late-bookings without creating duplicates — the unique constraint guards).
  3. Classify each: positive credit + 'ICG' in reference -> MATCHED, else IGNORED.
  4. For MATCHED: create a Donation row (if DONATIONS_AUTO_CREATE and an active
     campaign exists) and link it; otherwise leave the BankTransaction in REVIEW
     for a treasurer to attach manually.
  5. Update BankLink.last_synced_at on success.
"""

from __future__ import annotations

import logging
from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from apps.donations.models import Donation, DonationCampaign

from ..models import BankLink, BankTransaction
from .classifier import classify
from . import enable_banking

logger = logging.getLogger(__name__)

SYNC_OVERLAP_DAYS = 3
INITIAL_FETCH_DAYS = 30
CONSENT_WARN_DAYS = 14


def import_all_links() -> dict:
    """Sync every active BankLink. Returns a counts summary."""
    summary = {
        'links': 0, 'fetched': 0, 'created': 0,
        'donations': 0, 'review': 0, 'ignored': 0,
        'consent_warnings': 0, 'errors': 0,
    }
    for link in BankLink.objects.filter(is_active=True):
        summary['links'] += 1
        try:
            result = _import_one_link(link)
        except Exception:
            logger.exception("BankLink %s — unexpected import failure", link.id)
            summary['errors'] += 1
            continue
        for key in ('fetched', 'created', 'donations', 'review', 'ignored'):
            summary[key] += result.get(key, 0)
        if result.get('consent_warning'):
            summary['consent_warnings'] += 1
    return summary


def _import_one_link(link: BankLink) -> dict:
    counts = {
        'fetched': 0, 'created': 0,
        'donations': 0, 'review': 0, 'ignored': 0,
        'consent_warning': False,
    }
    now = timezone.now()

    if link.consent_valid_until:
        if link.consent_valid_until < now:
            logger.error(
                "BankLink %s — consent expired %s; skipping until re-linked.",
                link.id, link.consent_valid_until,
            )
            return counts
        if link.consent_valid_until < now + timedelta(days=CONSENT_WARN_DAYS):
            days_left = (link.consent_valid_until - now).days
            logger.warning(
                "BankLink %s — consent expires in %d days; re-link required soon.",
                link.id, days_left,
            )
            counts['consent_warning'] = True

    if link.provider != BankLink.PROVIDER_ENABLE_BANKING:
        logger.info(
            "BankLink %s — provider %s not yet implemented; skipping.",
            link.id, link.provider,
        )
        return counts

    date_from = _date_from_for(link, now)

    try:
        txns_iter = enable_banking.get_transactions(
            account_id=link.provider_account_id,
            date_from=date_from,
        )
        for txn in txns_iter:
            counts['fetched'] += 1
            bt, created = _store(link, txn)
            if not created or bt is None:
                continue
            counts['created'] += 1
            if bt.status == BankTransaction.STATUS_MATCHED:
                counts['donations'] += 1
            elif bt.status == BankTransaction.STATUS_REVIEW:
                counts['review'] += 1
            elif bt.status == BankTransaction.STATUS_IGNORED:
                counts['ignored'] += 1
    except enable_banking.EnableBankingError as e:
        logger.error("BankLink %s — fetch failed: %s", link.id, e)
        return counts

    link.last_synced_at = now
    link.save(update_fields=['last_synced_at'])
    return counts


def _date_from_for(link: BankLink, now):
    if link.last_synced_at:
        return (link.last_synced_at - timedelta(days=SYNC_OVERLAP_DAYS)).date()
    return (now - timedelta(days=INITIAL_FETCH_DAYS)).date()


@transaction.atomic
def _store(link, txn):
    """Insert one BankTransaction; auto-create a Donation when classifier matches.

    Returns (BankTransaction, created_bool). created=False means the txn_id was
    already imported by an earlier run — the caller skips it cleanly.
    """
    if not txn.transaction_id:
        logger.warning(
            "Skipping txn on link %s — no transaction_id (cannot dedupe).",
            link.id,
        )
        return None, False

    existing = BankTransaction.objects.filter(transaction_id=txn.transaction_id).first()
    if existing:
        return existing, False

    classification = classify(txn)
    bt = BankTransaction.objects.create(
        link=link,
        transaction_id=txn.transaction_id,
        booked_on=txn.booked_on,
        value_on=txn.value_on,
        amount=txn.amount,
        currency=txn.currency,
        counterparty_name=txn.counterparty_name,
        counterparty_iban=txn.counterparty_iban,
        remittance=txn.remittance,
        raw=txn.raw or {},
        status=classification,
    )

    if classification == BankTransaction.STATUS_MATCHED:
        _maybe_create_donation(bt)

    return bt, True


def _maybe_create_donation(bt: BankTransaction):
    """Convert a MATCHED BankTransaction into a Donation.

    Downgrades to REVIEW when DONATIONS_AUTO_CREATE is off, or when no active
    campaign exists — the treasurer attaches the donation manually from the
    review page in those cases.
    """
    if not getattr(settings, 'DONATIONS_AUTO_CREATE', True):
        bt.status = BankTransaction.STATUS_REVIEW
        bt.save(update_fields=['status'])
        return

    campaign = (
        DonationCampaign.objects
        .filter(is_active=True)
        .order_by('-created_at')
        .first()
    )
    if campaign is None:
        logger.info(
            "BankTransaction %s matched ICG but no active campaign — moving to review.",
            bt.id,
        )
        bt.status = BankTransaction.STATUS_REVIEW
        bt.save(update_fields=['status'])
        return

    user = _match_user(bt)
    donation = Donation.objects.create(
        campaign=campaign,
        user=user,
        donor_name='' if user else bt.counterparty_name,
        amount=bt.amount,
        donated_on=bt.booked_on,
        note=(bt.remittance or '')[:200],
        source=Donation.SOURCE_BANK,
        logged_by=None,
    )
    bt.donation = donation
    bt.save(update_fields=['donation'])


def _match_user(bt: BankTransaction):
    """Best-effort donor -> User mapping. Conservative on purpose: only match
    when there is EXACTLY ONE candidate by (first_name, last_name). Ambiguous
    matches leave user=None so the public wall shows counterparty_name and a
    treasurer can correct it in admin.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    name = (bt.counterparty_name or '').strip()
    if not name:
        return None
    parts = name.split()
    if len(parts) < 2:
        return None
    first, last = parts[0], parts[-1]
    candidates = User.objects.filter(
        first_name__iexact=first,
        last_name__iexact=last,
    )
    if candidates.count() == 1:
        return candidates.first()
    return None
