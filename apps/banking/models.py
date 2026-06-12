from decimal import Decimal

from django.db import models


class BankLink(models.Model):
    """One linked external bank account. The treasurer authorises this through
    the AISP provider's redirect flow (currently Enable Banking); we store the
    provider's session/account references and the PSD2 consent expiry so the
    next sync knows whether to fetch or prompt for re-link."""

    PROVIDER_ENABLE_BANKING = 'enable_banking'
    PROVIDER_CSV = 'csv'
    PROVIDER_CHOICES = [
        (PROVIDER_ENABLE_BANKING, 'Enable Banking'),
        (PROVIDER_CSV, 'CSV upload (manual)'),
    ]

    label = models.CharField(
        max_length=80,
        help_text="Display name, e.g. 'Club N26'.",
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        default=PROVIDER_ENABLE_BANKING,
    )
    institution_id = models.CharField(
        max_length=80, blank=True,
        help_text="Provider's bank identifier, e.g. 'N26_NTSBDEB1'.",
    )
    iban = models.CharField(max_length=34, blank=True)
    provider_session_id = models.CharField(
        max_length=128, blank=True,
        help_text="Provider's session/requisition ID for this consent.",
    )
    provider_account_id = models.CharField(
        max_length=128, blank=True,
        help_text="Provider's internal account ID used to fetch transactions.",
    )
    consent_valid_until = models.DateTimeField(
        null=True, blank=True,
        help_text="PSD2 consent expiry. Below 14 days = surface re-link banner.",
    )
    last_synced_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.label or f"BankLink #{self.pk}"


class BankTransaction(models.Model):
    """One transaction fetched from the linked bank. Append-only — never edited
    after insert. The classifier sets `status`; matched candidates also link to
    a Donation row."""

    STATUS_NEW = 'new'
    STATUS_MATCHED = 'matched'
    STATUS_IGNORED = 'ignored'
    STATUS_REVIEW = 'review'
    STATUS_CHOICES = [
        (STATUS_NEW, 'New'),
        (STATUS_MATCHED, 'Matched'),
        (STATUS_IGNORED, 'Ignored'),
        (STATUS_REVIEW, 'Needs review'),
    ]

    link = models.ForeignKey(
        BankLink, on_delete=models.PROTECT, related_name='transactions',
    )
    transaction_id = models.CharField(
        max_length=128, unique=True,
        help_text="Provider's stable transaction identifier. Idempotency key.",
    )
    booked_on = models.DateField()
    value_on = models.DateField(null=True, blank=True)
    amount = models.DecimalField(
        max_digits=10, decimal_places=2,
        help_text="Signed. Positive = credit (received).",
    )
    currency = models.CharField(max_length=3, default='EUR')
    counterparty_name = models.CharField(max_length=140, blank=True)
    counterparty_iban = models.CharField(max_length=34, blank=True)
    remittance = models.TextField(
        blank=True,
        help_text="Free-text reference. We grep for 'ICG' here.",
    )
    raw = models.JSONField(default=dict, blank=True)

    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=STATUS_NEW,
    )
    donation = models.OneToOneField(
        'donations.Donation', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='bank_transaction',
    )
    imported_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-booked_on', '-id']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['link', 'booked_on']),
        ]

    def __str__(self):
        sign = '+' if self.amount >= Decimal('0') else ''
        name = self.counterparty_name or '(unknown)'
        return f"{self.booked_on} {name} {sign}{self.amount} {self.currency}"
