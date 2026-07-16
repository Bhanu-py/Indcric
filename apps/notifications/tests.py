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
        saturday = date(2026, 6, 20)
        sunday = date(2026, 6, 21)
        s = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=saturday, date_option_1=saturday, date_option_2=sunday,
            time=time(18, 0), location="Hall",
        )
        return Poll.objects.create(session=s)

    def test_vote_emits_rsvp(self):
        Vote.objects.create(poll=self._poll(), user=self.donor, choice='yes')
        ev = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_RSVP).first()
        self.assertIsNotNone(ev)
        self.assertIn("Riya", ev.body)
        self.assertIn("picked Saturday", ev.body)
        self.assertEqual(ev.actor, self.donor)

    def test_vote_change_refreshes_single_row(self):
        v = Vote.objects.create(poll=self._poll(), user=self.donor, choice='yes')
        v.choice = 'no'
        v.save()
        rows = ActivityEvent.objects.filter(kind=ActivityEvent.KIND_RSVP)
        self.assertEqual(rows.count(), 1)          # deduped on the vote, not spammed
        self.assertIn("picked Sunday", rows.first().body)

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

from datetime import timedelta

from django.test import override_settings

from apps.notifications.models import BotEvent, OutboundMessage, WhatsAppIdentity


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
        saturday = date(2026, 6, 20)
        sunday = date(2026, 6, 21)
        self.session = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=saturday, date_option_1=saturday, date_option_2=sunday,
            time=time(18, 0), location="Hall",
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


@override_settings(BOT_INBOUND_TOKEN='tok', WHATSAPP_BOT_NUMBER='+32465110367',
                   WHATSAPP_GROUP_BOT_ENABLED=False)
class GroupInboundTests(TestCase):
    """The new /api/bot/inbound/ endpoint: records group votes, reacts ✅/❌,
    queues command replies, and makes ZERO Cloud-API calls for group traffic."""

    def setUp(self):
        self.member = User.objects.create_user(username="rohan", first_name="Rohan", password="x")
        self.member.phone = "+32470000001"
        self.member.save()
        saturday = date(2026, 6, 20)
        sunday = date(2026, 6, 21)
        self.session = Session.objects.create(
            name="Sunday Nets", duration=Decimal("2"),
            date=saturday, date_option_1=saturday, date_option_2=sunday,
            time=time(18, 0), location="Hall",
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
    def test_group_typed_yes_is_not_a_vote(self, mock_send):
        # Typed 'yes' in the group is conversation, not an RSVP — must NOT record
        # (members say yes/no all the time). Votes come from poll + reactions only.
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g2', 'text': 'YES', 'kind': 'text'})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Vote.objects.filter(poll=self.poll, user=self.member).exists())
        self.assertEqual(resp.json()['actions'], [])
        mock_send.assert_not_called()

    @patch("apps.notifications.services.send_text_message")
    def test_group_random_text_ignored_silently(self, mock_send):
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g2b', 'text': 'see you there!'})
        self.assertEqual(resp.status_code, 200)
        self.assertFalse(Vote.objects.exists())
        self.assertFalse(OutboundMessage.objects.exists())  # no "didn't understand" spam
        mock_send.assert_not_called()

    @patch("apps.notifications.services.send_text_message")
    def test_group_status_reports_all_availability_counts(self, mock_send):
        sunday = User.objects.create_user(username="sam", first_name="Sam", password="x")
        both = User.objects.create_user(username="jaya", first_name="Jaya", password="x")
        Vote.objects.create(poll=self.poll, user=self.member, choice='yes')
        Vote.objects.create(poll=self.poll, user=sunday, choice='no')
        Vote.objects.create(poll=self.poll, user=both, choice='all')
        unavailable = User.objects.create_user(username="lee", first_name="Lee", password="x")
        Vote.objects.create(poll=self.poll, user=unavailable, choice='out')

        resp = self._post({'from': '32470000001', 'wa_message_id': 'g-status', 'text': 'status', 'kind': 'text'})

        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['result'], {'kind': 'command', 'command': 'status'})
        msg = OutboundMessage.objects.get(target='community')
        self.assertIn("*4 voted* · Saturday 1 · Sunday 1 · Both 1 · Not available 1", msg.body)
        self.assertIn("*SATURDAY* (1)", msg.body)
        self.assertIn("*SUNDAY* (1)", msg.body)
        self.assertIn("*BOTH* (1)", msg.body)
        self.assertIn("*NOT AVAILABLE* (1)", msg.body)
        mock_send.assert_not_called()

    @patch("apps.notifications.services.send_text_message")
    def test_reaction_on_bot_message_records_yes_and_reacts(self, mock_send):
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g2c', 'kind': 'reaction', 'emoji': '👍'})
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
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g4', 'kind': 'poll_vote', 'selected': ['Sunday']})
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='no').exists()
        )
        self.assertEqual(resp.json()['actions'][0]['emoji'], '✅')

    def test_poll_vote_records_not_available(self):
        resp = self._post({'from': '32470000001', 'wa_message_id': 'g4out', 'kind': 'poll_vote', 'selected': ['Not available']})
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='out').exists()
        )
        self.assertEqual(resp.json()['actions'][0]['emoji'], '❌')

    @patch("apps.notifications.services.send_text_message")
    def test_one_day_poll_vote_no_records_no_and_reacts_cross(self, mock_send):
        self.poll.is_open = False
        self.poll.save(update_fields=['is_open'])
        sunday = timezone.localdate() + timedelta(days=1)
        one_day = Session.objects.create(
            name="Sunday Only", duration=Decimal("2"),
            date=sunday, date_option_2=sunday, final_play_day='sun',
            time=time(18, 0), location="Hall",
        )
        poll = Poll.objects.create(session=one_day)

        resp = self._post({'from': '32470000001', 'wa_message_id': 'g4b', 'kind': 'poll_vote', 'selected': ['No']})

        self.assertTrue(
            Vote.objects.filter(poll=poll, user=self.member, choice='no').exists()
        )
        self.assertEqual(resp.json()['actions'][0]['emoji'], '❌')
        mock_send.assert_not_called()

    def test_group_vote_matched_by_wa_name_learns_lid(self):
        # First-ever vote from a member: no wa_lid yet, but the roster set their
        # wa_name. Match by name, record the vote, and LEARN their LID.
        self.member.wa_name = 'Bhanu Angam'
        self.member.wa_lid = ''
        self.member.save()
        resp = self._post({
            'from': '+267418135986186', 'lid': '267418135986186',
            'author_name': 'Bhanu Angam', 'wa_message_id': 'gname1',
            'kind': 'poll_vote', 'selected': ['Saturday'],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='yes').exists()
        )
        self.member.refresh_from_db()
        self.assertEqual(self.member.wa_lid, '267418135986186')  # learned

    def test_group_vote_matched_by_lid_when_phone_hidden(self):
        # Community/privacy groups expose only a LID, never the phone — match on
        # User.wa_lid. The 'from' here is the opaque LID-derived value (no phone
        # match); the lid links it to the member.
        self.member.wa_lid = '267418135986186'
        self.member.save()
        resp = self._post({
            'from': '+267418135986186', 'lid': '267418135986186',
            'wa_message_id': 'glid1', 'kind': 'poll_vote', 'selected': ['Saturday'],
        })
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(
            Vote.objects.filter(poll=self.poll, user=self.member, choice='yes').exists()
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
        p = {'from': '32470000001', 'wa_message_id': 'g7', 'kind': 'reaction', 'emoji': '👎'}
        self._post(p)
        self._post(p)  # same wa_message_id → BotEvent unique swallows it
        self.assertEqual(
            Vote.objects.filter(poll=self.poll, user=self.member).count(), 1
        )


@override_settings(BOT_WEBHOOK_TOKEN='wtok')
class OutboundQueueTests(TestCase):
    """The group-post queue the Node bot drains: claim, reclaim-stale, ack."""

    def setUp(self):
        self.drain = reverse('bot_outbound')
        self.ack = reverse('bot_outbound_ack')

    def test_drain_requires_token(self):
        OutboundMessage.objects.create(body='hi', target='community')
        self.assertEqual(self.client.get(f"{self.drain}?token=wrong").status_code, 401)

    def test_drain_claims_pending(self):
        m = OutboundMessage.objects.create(body='RSVP please', target='community')
        resp = self.client.get(f"{self.drain}?token=wtok")
        self.assertEqual(resp.status_code, 200)
        msgs = resp.json()['messages']
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['body'], 'RSVP please')
        m.refresh_from_db()
        self.assertEqual(m.status, OutboundMessage.CLAIMED)
        self.assertIsNotNone(m.claimed_at)

    def test_drain_skips_freshly_claimed(self):
        OutboundMessage.objects.create(
            body='x', status=OutboundMessage.CLAIMED, claimed_at=timezone.now(),
        )
        self.assertEqual(self.client.get(f"{self.drain}?token=wtok").json()['messages'], [])

    def test_drain_reclaims_stale_claimed(self):
        stale = OutboundMessage.objects.create(
            body='stuck', status=OutboundMessage.CLAIMED,
            claimed_at=timezone.now() - timedelta(seconds=200),
        )
        ids = [m['id'] for m in self.client.get(f"{self.drain}?token=wtok").json()['messages']]
        self.assertIn(stale.id, ids)

    def test_ack_sent_marks_sent_and_audits(self):
        m = OutboundMessage.objects.create(
            body='x', status=OutboundMessage.CLAIMED, claimed_at=timezone.now(),
        )
        resp = self.client.post(
            f"{self.ack}?token=wtok",
            data=json.dumps({'id': m.id, 'status': 'sent', 'wa_message_id': 'wamid.out1'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.status, OutboundMessage.SENT)
        self.assertIsNotNone(m.sent_at)
        self.assertTrue(
            BotEvent.objects.filter(action='group_post', direction=BotEvent.OUTBOUND).exists()
        )

    def test_ack_failed_increments_attempts(self):
        m = OutboundMessage.objects.create(
            body='x', status=OutboundMessage.CLAIMED, claimed_at=timezone.now(),
        )
        resp = self.client.post(
            f"{self.ack}?token=wtok",
            data=json.dumps({'id': m.id, 'status': 'failed', 'error': 'boom'}),
            content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        m.refresh_from_db()
        self.assertEqual(m.status, OutboundMessage.FAILED)
        self.assertEqual(m.attempts, 1)
        self.assertEqual(m.error, 'boom')


@override_settings(WHATSAPP_GROUP_BOT_ENABLED=True)
class AutoPostEnqueueTests(TestCase):
    """Domain events auto-queue group posts (gated on WHATSAPP_GROUP_BOT_ENABLED)."""

    def _session(self, **kw):
        # Future date so the poll counts as 'upcoming' (the group RSVP poll only
        # auto-posts for upcoming sessions). Relative to today, not hardcoded.
        defaults = dict(
            name="Sunday Nets", duration=Decimal("2"),
            date=timezone.localdate() + timedelta(days=7), time=time(18, 0),
            location="Hall",
        )
        defaults.update(kw)
        return Session.objects.create(**defaults)

    def test_poll_open_enqueues_native_poll(self):
        saturday = timezone.localdate() + timedelta(days=6)
        sunday = timezone.localdate() + timedelta(days=7)
        s = self._session(date=saturday, date_option_1=saturday, date_option_2=sunday)
        Poll.objects.create(session=s)
        m = OutboundMessage.objects.filter(dedup_key=f'poll_opened:{s.poll.id}').first()
        self.assertIsNotNone(m)
        self.assertEqual(m.kind, OutboundMessage.POLL)
        self.assertEqual(m.poll_options, ['Saturday', 'Sunday', 'Both', 'Not available'])
        self.assertIn("Sunday Nets", m.body)

    def test_one_day_poll_open_enqueues_yes_no_native_poll(self):
        sunday = timezone.localdate() + timedelta(days=7)
        s = self._session(date=sunday, date_option_2=sunday, final_play_day='sun')
        Poll.objects.create(session=s)
        m = OutboundMessage.objects.filter(dedup_key=f'poll_opened:{s.poll.id}').first()
        self.assertIsNotNone(m)
        self.assertEqual(m.kind, OutboundMessage.POLL)
        self.assertEqual(m.poll_options, ['Yes', 'No'])
        self.assertIn("can you play on Sunday", m.body)

    def test_past_session_poll_does_not_enqueue(self):
        s = self._session(date=date(2020, 1, 1))
        Poll.objects.create(session=s)
        self.assertFalse(OutboundMessage.objects.exists())

    def test_session_confirmed_enqueues_cost_split_text(self):
        s = self._session(cost=Decimal("20"))
        s.cost_per_person = Decimal("5.00")
        s.attendance_confirmed = True
        s.save()
        m = OutboundMessage.objects.filter(dedup_key=f'session_confirmed:{s.id}').first()
        self.assertIsNotNone(m)
        self.assertEqual(m.kind, OutboundMessage.TEXT)
        self.assertIn("€5.00 per player", m.body)

    def test_confirm_twice_does_not_double_post(self):
        s = self._session(cost=Decimal("20"))
        s.cost_per_person = Decimal("5.00")
        s.attendance_confirmed = True
        s.save()
        s.save()  # re-save while confirmed
        self.assertEqual(
            OutboundMessage.objects.filter(dedup_key=f'session_confirmed:{s.id}').count(), 1
        )

    @override_settings(WHATSAPP_GROUP_BOT_ENABLED=False)
    def test_disabled_enqueues_nothing(self):
        s = self._session()
        Poll.objects.create(session=s)
        self.assertFalse(OutboundMessage.objects.exists())


@override_settings(BOT_WEBHOOK_TOKEN='wtok')
class RosterAndIdentityTests(TestCase):
    """LID onboarding: bulk roster import + mapping an identity to a user."""

    def test_roster_requires_token(self):
        resp = self.client.post(
            reverse('bot_roster') + '?token=bad',
            data=json.dumps({'members': []}), content_type='application/json',
        )
        self.assertEqual(resp.status_code, 401)

    def test_roster_stages_lids(self):
        resp = self.client.post(
            reverse('bot_roster') + '?token=wtok',
            data=json.dumps({'members': [
                {'lid': '267418135986186', 'name': 'Bhanu'},
                {'lid': '8826174587110', 'name': 'Sam'},
            ]}), content_type='application/json',
        )
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['staged'], 2)
        self.assertTrue(
            WhatsAppIdentity.objects.filter(lid='267418135986186', name='Bhanu').exists()
        )

    def test_roster_links_wa_name_by_phone(self):
        u = User.objects.create_user(username='bhanu', password='x')
        u.phone = '+32470756917'
        u.save()
        resp = self.client.post(
            reverse('bot_roster') + '?token=wtok',
            data=json.dumps({'members': [
                {'phone': '+32470756917', 'name': 'Bhanu Angam'},
            ]}), content_type='application/json',
        )
        self.assertEqual(resp.json()['linked'], 1)
        u.refresh_from_db()
        self.assertEqual(u.wa_name, 'Bhanu Angam')

    def test_mapping_identity_sets_user_wa_lid(self):
        u = User.objects.create_user(username='bhanu', password='x')
        ident = WhatsAppIdentity.objects.create(lid='267418135986186', name='Bhanu')
        ident.user = u
        ident.save()
        u.refresh_from_db()
        self.assertEqual(u.wa_lid, '267418135986186')  # mirrored for vote matching
