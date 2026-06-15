"""Tests for the WhatsApp bot 'History' command (issue #30).

HISTORY shows a player's recent matches (batting/bowling from the ball-by-ball
ledger) + per-session cost + a career summary + wallet. Stats come from
apps.matches.scoring, NOT the (unused) Payment table.
"""
from datetime import date, time
from decimal import Decimal
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.test import TestCase

from apps.matches.models import Delivery, Innings, Match, Player, Team
from apps.notifications import bot_messages
from apps.notifications.views import _handle_history
from apps.payments.models import Wallet
from apps.sessions.models import Session, SessionPlayer

User = get_user_model()

EMPTY_CAREER = {'batting': {'innings': 0}, 'bowling': {'wickets': 0, 'best': None}, 'matches': 0}


class HistoryMessageTests(TestCase):
    """The pure message builder — no DB."""

    def test_empty_history(self):
        msg = bot_messages.history([], EMPTY_CAREER, Decimal("0.00"))
        self.assertIn("No games on record", msg)

    def test_lists_games_career_and_wallet(self):
        games = [
            {'session': 'Sunday Nets', 'match': 'Match 1', 'date': 'Sun 14 Jun',
             'runs': 42, 'balls': 28, 'wickets': 2, 'won': True,
             'amount': Decimal("7.20"), 'paid': False},
            {'session': 'Friday KO', 'match': 'Match 1', 'date': 'Fri 12 Jun',
             'runs': 5, 'balls': 6, 'wickets': 0, 'won': False,
             'amount': None, 'paid': True},
        ]
        career = {'batting': {'innings': 2, 'runs': 47, 'hs_label': '42'},
                  'bowling': {'wickets': 2, 'best': '2/14'}, 'matches': 2}
        msg = bot_messages.history(games, career, Decimal("12.00"))
        self.assertIn("Your last 2 games", msg)
        self.assertIn("Sunday Nets", msg)
        self.assertIn("42 (28)", msg)
        self.assertIn("2 wkts", msg)
        self.assertIn("won", msg)
        self.assertIn("€7.20 due", msg)
        self.assertIn("€—", msg)            # None amount renders as a dash
        self.assertIn("Career", msg)
        self.assertIn("47 runs", msg)
        self.assertIn("Wallet: €12.00", msg)


class HandleHistoryTests(TestCase):
    def setUp(self):
        self.phone = "+32470000000"
        self.user = User.objects.create_user(username="bhanu", password="x")
        self.user.phone = self.phone
        self.user.save()
        opp = User.objects.create_user(username="opp", password="x")
        session = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=date(2026, 6, 14), time=time(18, 0), location="Hall",
            cost_per_person=Decimal("7.20"),
        )
        SessionPlayer.objects.create(session=session, user=self.user, paid=False)
        match = Match.objects.create(session=session, name="Match 1")
        t1 = Team.objects.create(match=match, name="A")
        t2 = Team.objects.create(match=match, name="B")
        p_user = Player.objects.create(user=self.user, team=t1, role="bat")
        p_opp = Player.objects.create(user=opp, team=t2, role="bowl")
        inn = Innings.objects.create(match=match, number=1, batting_team=t1, bowling_team=t2)
        # user faces 2 balls for 6 runs (4 then 2)
        Delivery.objects.create(innings=inn, sequence=1, striker=p_user, bowler=p_opp, runs_off_bat=4)
        Delivery.objects.create(innings=inn, sequence=2, striker=p_user, bowler=p_opp, runs_off_bat=2)
        Wallet.objects.create(user=self.user, amount=Decimal("12.00"))

    @patch("apps.notifications.services.send_text_message")
    def test_reply_has_stats_and_wallet(self, mock_send):
        _handle_history("wamid.h1", self.phone, {"text": "History"})
        self.assertTrue(mock_send.called)
        sent = mock_send.call_args[0][1]
        self.assertIn("Sunday Nets", sent)
        self.assertIn("6 (2)", sent)        # 6 runs off 2 balls
        self.assertIn("Career", sent)
        self.assertIn("Wallet: €12.00", sent)

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
        self.assertEqual(mock_send.call_count, 1)     # no second send
