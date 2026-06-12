from datetime import date
from decimal import Decimal

from django.test import TestCase

from apps.banking.models import BankTransaction
from apps.banking.services.base import Transaction
from apps.banking.services.classifier import ICG_PATTERN, classify


class ClassifierTests(TestCase):
    def _txn(self, *, amount, remittance):
        return Transaction(
            transaction_id='t1',
            booked_on=date(2026, 6, 12),
            amount=Decimal(amount),
            currency='EUR',
            remittance=remittance,
        )

    def test_icg_credit_is_matched(self):
        self.assertEqual(
            classify(self._txn(amount='25.00', remittance='ICG donation - John')),
            BankTransaction.STATUS_MATCHED,
        )

    def test_lowercase_icg_is_matched(self):
        self.assertEqual(
            classify(self._txn(amount='10.00', remittance='donation icg / Bhanu')),
            BankTransaction.STATUS_MATCHED,
        )

    def test_no_icg_is_ignored(self):
        self.assertEqual(
            classify(self._txn(amount='50.00', remittance='Salary May')),
            BankTransaction.STATUS_IGNORED,
        )

    def test_substring_does_not_match(self):
        # 'ricgardo' contains 'icg' but not as a whole word.
        self.assertEqual(
            classify(self._txn(amount='5.00', remittance='from ricgardo')),
            BankTransaction.STATUS_IGNORED,
        )

    def test_negative_amount_is_ignored(self):
        self.assertEqual(
            classify(self._txn(amount='-20.00', remittance='ICG refund')),
            BankTransaction.STATUS_IGNORED,
        )

    def test_zero_amount_is_ignored(self):
        self.assertEqual(
            classify(self._txn(amount='0.00', remittance='ICG donation')),
            BankTransaction.STATUS_IGNORED,
        )

    def test_pattern_handles_punctuation_boundaries(self):
        # Word boundaries treat '-', '/', '.' as separators.
        self.assertIsNotNone(ICG_PATTERN.search('Don. ICG/Bhanu'))
        self.assertIsNotNone(ICG_PATTERN.search('ICG-2026'))
        self.assertIsNone(ICG_PATTERN.search('icgardo'))
