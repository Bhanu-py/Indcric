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


# ─────────────────────────── Activity feed ───────────────────────────

from django.urls import reverse
from django.utils import timezone

from apps.donations.models import Donation, DonationCampaign
from apps.notifications.models import (
    ActivityEvent, ActivityFeedState, unread_count_for,
)
from apps.payments.models import Payment
from apps.polls.models import Poll, Vote


class ActivityEmitTests(TestCase):
    """Domain events flow into the feed via signals."""

    def setUp(self):
        self.donor = User.objects.create_user(username="riya", first_name="Riya", password="x")
        self.campaign = DonationCampaign.objects.create(title="Server fund", goal_amount=Decimal("100"))

    def test_donation_emits_activity(self):
        Donation.objects.create(campaign=self.campaign, user=self.donor, amount=Decimal("25.00"))
        ev = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_DONATION).first()
        self.assertIsNotNone(ev)
        self.assertIn("Riya", ev.body)
        self.assertIn("€25.00", ev.body)
        self.assertEqual(ev.actor, self.donor)

    def test_anonymous_donation_hides_donor(self):
        Donation.objects.create(
            campaign=self.campaign, user=self.donor, amount=Decimal("10.00"), is_anonymous=True
        )
        ev = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_DONATION).first()
        self.assertIn("Anonymous", ev.body)
        self.assertIsNone(ev.actor)            # no actor link for an anonymous gift
        self.assertNotIn("Riya", ev.body)

    def test_session_created_emits_activity(self):
        Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=date(2026, 6, 21), time=time(18, 0), location="Hall",
        )
        self.assertTrue(
            ActivityEvent.objects.filter(kind=ActivityEvent.KIND_SESSION, body__icontains="Sunday Nets").exists()
        )

    def _poll(self):
        s = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=date(2026, 6, 21), time=time(18, 0), location="Hall",
        )
        return Poll.objects.create(session=s)

    def test_vote_emits_rsvp(self):
        Vote.objects.create(poll=self._poll(), user=self.donor, choice='yes')
        ev = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_RSVP).first()
        self.assertIsNotNone(ev)
        self.assertIn("Riya", ev.body)
        self.assertIn("in for", ev.body)
        self.assertEqual(ev.actor, self.donor)

    def test_vote_change_refreshes_single_row(self):
        v = Vote.objects.create(poll=self._poll(), user=self.donor, choice='yes')
        v.choice = 'no'
        v.save()
        rows = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_RSVP)
        self.assertEqual(rows.count(), 1)          # deduped on the vote, not spammed
        self.assertIn("out of", rows.first().body)

    def test_vote_withdraw_removes_row(self):
        v = Vote.objects.create(poll=self._poll(), user=self.donor, choice='yes')
        v.delete()
        self.assertFalse(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_RSVP).exists())

    def test_attendance_confirmed_emits_cost_split(self):
        """Confirming attendance on a paid session posts a settlement / cost-split
        event (Payments), not a forward-looking 'see you there'."""
        s = Session.objects.create(
            name="Friday KO", cost=Decimal("20"), duration=Decimal("2"),
            date=date(2026, 5, 30), time=time(18, 0), location="Hall",
        )
        # Mirror the attendance-save: per-person split computed, then confirmed.
        s.cost_per_person = Decimal("5.00")
        s.attendance_confirmed = True
        s.save()
        ev = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_PAYMENT).first()
        self.assertIsNotNone(ev)
        self.assertIn("€5.00 per player", ev.body)     # the price, up front
        self.assertEqual(ev.action_label, 'Pay')        # Pay CTA, not just View
        self.assertNotIn("see you there", ev.body)

    def test_free_session_confirmed_emits_nothing(self):
        """A free session (no cost to split) gets no payments-due entry."""
        s = Session.objects.create(
            name="Free knock", cost=Decimal("0"), duration=Decimal("2"),
            date=date(2026, 5, 30), time=time(18, 0), location="Hall",
        )
        before = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_PAYMENT).count()
        s.attendance_confirmed = True   # no cost_per_person set
        s.save()
        self.assertEqual(
            ActivityEvent.objects.filter(kind=ActivityEvent.KIND_PAYMENT).count(), before
        )

    def test_payment_paid_emits_once(self):
        s = Session.objects.create(
            name="Pay session", duration=Decimal("2"),
            date=date(2026, 6, 20), time=time(18, 0), location="Hall",
        )
        p = Payment.objects.create(user=self.donor, session=s, amount=Decimal("8.00"), status='paid')
        self.assertEqual(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_PAYMENT).count(), 1)
        p.save()  # re-save while paid → deduped, no second row
        self.assertEqual(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_PAYMENT).count(), 1)

    def test_pending_payment_does_not_emit(self):
        s = Session.objects.create(
            name="Pending session", duration=Decimal("2"),
            date=date(2026, 6, 22), time=time(18, 0), location="Hall",
        )
        Payment.objects.create(user=self.donor, session=s, amount=Decimal("8.00"), status='pending')
        self.assertFalse(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_PAYMENT).exists())

    def test_match_completion_emits_once_and_refreshes(self):
        s = Session.objects.create(
            name="Match day", duration=Decimal("2"),
            date=date(2026, 6, 14), time=time(18, 0), location="Hall",
        )
        match = Match.objects.create(session=s, name="Match 1")
        t1 = Team.objects.create(match=match, name="A")
        t2 = Team.objects.create(match=match, name="B")
        Innings.objects.create(match=match, number=1, batting_team=t1, bowling_team=t2, is_closed=True)
        Innings.objects.create(match=match, number=2, batting_team=t2, bowling_team=t1, is_closed=True)
        # Complete now, but the result only posts when the match is saved with a
        # winner (as finalize_match_result does) — not on innings save.
        self.assertFalse(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_MATCH).exists())

        match.winner = t1
        match.save()
        self.assertEqual(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_MATCH).count(), 1)
        ev = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_MATCH).first()
        self.assertIn("A won", ev.body)

        # Reopen + re-finalize with a corrected winner → same row, refreshed body.
        match.winner = t2
        match.save()
        self.assertEqual(ActivityEvent.objects.filter(kind=ActivityEvent.KIND_MATCH).count(), 1)
        ev.refresh_from_db()
        self.assertIn("B won", ev.body)

    def test_deleting_target_cascades_feed_events(self):
        """Deleting a session removes its feed rows — no orphans with dead links."""
        s = Session.objects.create(
            name="ToDelete", duration=Decimal("2"),
            date=date(2026, 6, 1), time=time(18, 0), location="H",
        )
        self.assertTrue(ActivityEvent.objects.filter(body__icontains="ToDelete").exists())
        s.delete()
        self.assertFalse(ActivityEvent.objects.filter(body__icontains="ToDelete").exists())


class ActivityUnreadTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="x")
        self.other = User.objects.create_user(username="actor", password="x")

    def test_unread_counts_events_after_seen_excluding_own(self):
        ActivityEvent.objects.create(kind=ActivityEvent.KIND_PING, body="by other", actor=self.other)
        ActivityEvent.objects.create(kind=ActivityEvent.KIND_PING, body="by me", actor=self.user)
        # Own action excluded → only the 'other' event counts.
        self.assertEqual(unread_count_for(self.user), 1)

    def test_mark_all_read_clears_unread(self):
        ActivityEvent.objects.create(kind=ActivityEvent.KIND_PING, body="x", actor=self.other)
        self.assertEqual(unread_count_for(self.user), 1)
        state, _ = ActivityFeedState.objects.get_or_create(user=self.user)
        state.last_seen_at = timezone.now()
        state.save()
        self.assertEqual(unread_count_for(self.user), 0)


class ActivityViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="viewer", password="x")
        self.donation_ev = ActivityEvent.objects.create(kind=ActivityEvent.KIND_DONATION, body="Riya donated €25.00")
        self.payment_ev = ActivityEvent.objects.create(kind=ActivityEvent.KIND_PAYMENT, body="Sam paid €8.00")

    def test_feed_requires_login(self):
        resp = self.client.get(reverse('activity'))
        self.assertEqual(resp.status_code, 302)  # redirect to login

    def test_feed_renders_with_bell(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('activity'))
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "Activity")
        self.assertContains(resp, 'id="activity-bell"')   # header bell present
        self.assertContains(resp, "Riya donated")

    def test_tab_filter_returns_only_matching_kind(self):
        self.client.force_login(self.user)
        resp = self.client.get(reverse('activity'), {'tab': 'donations'}, HTTP_HX_REQUEST='true')
        self.assertContains(resp, "Riya donated")
        self.assertNotContains(resp, "Sam paid")

    def test_mark_all_read_view_resets_and_oob_bell(self):
        self.client.force_login(self.user)
        resp = self.client.post(reverse('activity_read_all'), {'tab': 'all'}, HTTP_HX_REQUEST='true')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'hx-swap-oob="true"')      # bell OOB update
        self.assertTrue(ActivityFeedState.objects.filter(user=self.user).exists())
        self.assertEqual(unread_count_for(self.user), 0)


# ─────────────────────── Group-bot Phase 1 (inbound) ───────────────────────

import json

from django.test import override_settings

from apps.notifications.models import OutboundMessage


@override_settings(WHATSAPP_APP_SECRET='')
class MetaPathCharacterizationTests(TestCase):
    """Lock the EXISTING Meta Cloud-API DM behaviour before/after the
    dispatch_inbound refactor: a webhook RSVP records a Vote AND sends a DM
    confirmation via send_text_message. If this breaks, the refactor regressed.

    WHATSAPP_APP_SECRET='' runs the webhook in dev mode (signature check skipped)
    — this test exercises dispatch, not signature verification."""

    def setUp(self):
        self.member = User.objects.create_user(username="rohan", first_name="Rohan", password="x")
        self.member.phone = "+32470000001"
        self.member.save()
        self.session = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=date(2026, 6, 21), time=time(18, 0), location="Hall",
        )
        self.poll = Poll.objects.create(session=self.session)

    @patch("apps.notifications.services.send_text_message")
    def test_meta_webhook_rsvp_records_vote_and_dms(self, mock_send):
        payload = {'entry': [{'changes': [{'value': {'messages': [
            {'id': 'm1', 'from': '32470000001', 'type': 'text', 'text': {'body': 'YES'}}
        ]}}]}]}
        resp = self.client.post(
            reverse('bot_whatsapp'), data=json.dumps(payload),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='yes').exists()
        )
        mock_send.assert_called_once()  # DM confirmation — Meta path unchanged


@override_settings(BOT_INBOUND_TOKEN='tok', WHATSAPP_BOT_NUMBER='+32465110367')
class GroupInboundTests(TestCase):
    """The new /api/bot/inbound/ endpoint: records group votes, reacts ✅/❌,
    queues command replies, and makes ZERO Cloud-API calls for group traffic."""

    def setUp(self):
        self.member = User.objects.create_user(username="rohan", first_name="Rohan", password="x")
        self.member.phone = "+32470000001"
        self.member.save()
        self.session = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=date(2026, 6, 21), time=time(18, 0), location="Hall",
        )
        self.poll = Poll.objects.create(session=self.session)
        self.url = reverse('bot_inbound')

    def _post(self, payload, token='tok'):
        return self.client.post(
            f"{self.url}?token={token}",
            data=json.dumps(payload), content_type='application/json',
        )

    def test_requires_token(self):
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g1', 'text': 'YES'}, token='wrong')
        self.assertEqual(resp.status_code, 401)
        self.assertFalse(Vote.objects.exists())

    @patch("apps.notifications.services.send_text_message")
    def test_group_text_yes_records_vote_reacts_and_no_cloud_calls(self, mock_send):
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g2', 'text': 'YES', 'kind': 'text'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='yes').exists()
        )
        self.assertEqual(resp.json()['actions'][0]['emoji'], '✅')
        mock_send.assert_not_called()

    @patch("apps.notifications.services.send_text_message")
    def test_skin_tone_reaction_records_yes(self, mock_send):
        # 👍🏾 — the skin-tone modifier must not defeat the match (Phase 0 bug).
        self._post({'from': '32470000001', 'wa_message_id': 'g3', 'kind': 'reaction', 'emoji': '👍🏾'})
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='yes').exists()
        )
        mock_send.assert_not_called()

    def test_poll_vote_records_no(self):
        self._post({'from': '32470000001', 'wa_message_id': 'g4', 'kind': 'poll_vote', 'selected': ['No ❌']})
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='no').exists()
        )

    @patch("apps.notifications.services.send_text_message")
    def test_group_help_from_unknown_queues_text_no_cloud_calls(self, mock_send):
        resp = self._post({'from': '32499999999', 'wa_message_id': 'g5', 'text': 'HELP'})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(OutboundMessage.objects.filter(target='community').exists())
        mock_send.assert_not_called()  # critical: no paid DM to a closed window

    def test_self_activity_ignored(self):
        resp = self._post({'from': '32465110367', 'wa_message_id': 'g6', 'kind': 'reaction', 'emoji': '✅'})
        self.assertEqual(resp.json().get('ignored'), 'self')
        self.assertFalse(Vote.objects.exists())

    def test_duplicate_inbound_is_idempotent(self):
        p = {'from': '32470000001', 'wa_message_id': 'g7', 'text': 'NO'}
        self._post(p)
        self._post(p)  # same wa_message_id → BotEvent unique swallows it
        self.assertEqual(
            Vote.objects.filter(poll=self.poll, user=self.member).count(), 1
        )
