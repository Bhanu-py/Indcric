"""Tests for the WhatsApp bot 'History' command (issue #30)."""
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.notifications import bot_messages
from apps.notifications.views import _handle_history
from apps.payments.models import Payment, Wallet
from apps.sessions.models import Session

User = get_user_model()


class HistoryMessageTests(TestCase):
    """The pure message builder — no DB."""

    def test_empty_history(self):
        msg = bot_messages.history([], Decimal("0.00"))
        self.assertIn("No games on record", msg)

    def test_lists_rows_and_wallet(self):
        rows = [
            ("Sunday Nets", "Sun 14 Jun", Decimal("7.20"), "paid"),
            ("Friday Knockout", "Fri 12 Jun", Decimal("9.50"), "pending"),
        ]
        msg = bot_messages.history(rows, Decimal("12.00"))
        self.assertIn("Your last 2 games", msg)
        self.assertIn("Sunday Nets", msg)
        self.assertIn("€7.20", msg)
        self.assertIn("pending", msg)
        self.assertIn("Wallet balance: €12.00", msg)


class HandleHistoryTests(TestCase):
    def setUp(self):
        self.phone = "+32470000000"
        self.user = User.objects.create_user(username="bhanu", password="x")
        self.user.phone = self.phone
        self.user.save()
        session = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=date(2026, 6, 14), time=time(18, 0), location="Hall",
        )
        Payment.objects.create(
            user=self.user, session=session, amount=Decimal("7.20"), status="paid",
        )
        Wallet.objects.create(user=self.user, amount=Decimal("12.00"))

    @patch("apps.notifications.services.send_text_message")
    def test_reply_contains_game_and_wallet(self, mock_send):
        _handle_history("wamid.h1", self.phone, {"text": "History"})
        self.assertTrue(mock_send.called)
        sent = mock_send.call_args[0][1]
        self.assertIn("Sunday Nets", sent)
        self.assertIn("€7.20", sent)
        self.assertIn("Wallet balance: €12.00", sent)

    @patch("apps.notifications.services.send_text_message")
    def test_unknown_phone_gets_not_recognised(self, mock_send):
        _handle_history("wamid.h2", "+32999999999", {})
        self.assertTrue(mock_send.called)
        self.assertIn("couldn't recognize", mock_send.call_args[0][1])

    @patch("apps.notifications.services.send_text_message")
    def test_duplicate_message_is_idempotent(self, mock_send):
        _handle_history("wamid.h3", self.phone, {})
        self.assertEqual(mock_send.call_count, 1)
        _handle_history("wamid.h3", self.phone, {})  # same wa_message_id
        self.assertEqual(mock_send.call_count, 1)  # no second send
