"""Tests for the staff match-delete guard (issue #39).

A played match (with a saved ball-by-ball scorecard) was wiped by an accidental
one-tap delete. delete_match_view now refuses to destroy a scored match unless
the staff re-types the match name in a `confirm_name` field.
"""
from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.matches.models import Delivery, Innings, Match, Player, Team
from apps.payments.models import Payment
from apps.polls.models import Poll, Vote
from apps.sessions.models import Attendance, Session, SessionPlayer

User = get_user_model()


class DeleteMatchGuardTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff", password="x", is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff)
        self.session = Session.objects.create(
            name="S", duration=Decimal("2"), date=date(2026, 6, 1),
            time=time(18, 0), location="H",
        )

    def _scored_match(self, name="Match 1"):
        m = Match.objects.create(session=self.session, name=name)
        t1 = Team.objects.create(match=m, name="A")
        t2 = Team.objects.create(match=m, name="B")
        p1 = Player.objects.create(user=self.staff, team=t1, role="bat")
        other = User.objects.create_user(username="p2", password="x")
        p2 = Player.objects.create(user=other, team=t2, role="bowl")
        inn = Innings.objects.create(match=m, number=1, batting_team=t1, bowling_team=t2)
        Delivery.objects.create(innings=inn, sequence=1, striker=p1, bowler=p2, runs_off_bat=1)
        return m

    def test_scored_match_not_deleted_without_confirm(self):
        m = self._scored_match()
        self.client.post(reverse("delete_match", args=[m.id]))
        self.assertTrue(Match.objects.filter(id=m.id).exists())

    def test_scored_match_not_deleted_with_wrong_name(self):
        m = self._scored_match()
        self.client.post(reverse("delete_match", args=[m.id]), {"confirm_name": "wrong"})
        self.assertTrue(Match.objects.filter(id=m.id).exists())

    def test_scored_match_deleted_with_correct_name(self):
        m = self._scored_match()
        self.client.post(reverse("delete_match", args=[m.id]), {"confirm_name": "Match 1"})
        self.assertFalse(Match.objects.filter(id=m.id).exists())

    def test_unscored_match_deletes_without_confirm(self):
        m = Match.objects.create(session=self.session, name="Empty")
        self.client.post(reverse("delete_match", args=[m.id]))
        self.assertFalse(Match.objects.filter(id=m.id).exists())


class DeleteSessionWithScoringTests(TestCase):
    """Deleting a session whose matches carry a ball-by-ball ledger must not
    500 on Delivery's PROTECT of Player (regression)."""

    def setUp(self):
        self.staff = User.objects.create_user(username="boss", password="x", is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff)
        self.session = Session.objects.create(
            name="Match day", duration=Decimal("2"), date=date(2026, 6, 1),
            time=time(18, 0), location="H",
        )

    def test_delete_session_with_ball_ledger(self):
        m = Match.objects.create(session=self.session, name="Match 1")
        t1 = Team.objects.create(match=m, name="A")
        t2 = Team.objects.create(match=m, name="B")
        p1 = Player.objects.create(user=self.staff, team=t1, role="bat")
        other = User.objects.create_user(username="p2", password="x")
        p2 = Player.objects.create(user=other, team=t2, role="bowl")
        inn = Innings.objects.create(match=m, number=1, batting_team=t1, bowling_team=t2)
        Delivery.objects.create(innings=inn, sequence=1, striker=p1, bowler=p2, runs_off_bat=4)

        resp = self.client.post(reverse("delete_session", args=[self.session.id]))
        self.assertEqual(resp.status_code, 302)
        self.assertFalse(Session.objects.filter(id=self.session.id).exists())
        self.assertFalse(Match.objects.filter(id=m.id).exists())
        self.assertFalse(Delivery.objects.exists())


class AvailabilityModeTests(TestCase):
    def setUp(self):
        self.staff = User.objects.create_user(username="staff2", password="x", is_staff=True)
        self.client = Client()
        self.client.force_login(self.staff)

    def test_create_session_allows_sunday_only_yes_no_poll(self):
        today = timezone.localdate()
        sunday = today + timedelta(days=(6 - today.weekday()) % 7 or 7)

        resp = self.client.post(reverse("create_session"), {
            "name": "",
            "date_option_1": "",
            "date_option_2": sunday.isoformat(),
            "time": "18:00",
            "duration": "3",
            "location": "Henry Storyplein",
            "cost": "80",
        })

        self.assertEqual(resp.status_code, 302)
        session = Session.objects.get()
        self.assertIsNone(session.date_option_1)
        self.assertEqual(session.date_option_2, sunday)
        self.assertEqual(session.date, sunday)
        self.assertEqual(session.final_play_day, "sun")
        self.assertEqual(session.poll.question, f"Can you play on {session.single_play_day_label}?")

    def test_two_day_web_vote_stores_sat_sun_codes(self):
        user = User.objects.create_user(username="voter", password="x")
        self.client.force_login(user)
        saturday = timezone.localdate() + timedelta(days=5)
        sunday = timezone.localdate() + timedelta(days=6)
        session = Session.objects.create(
            name="Weekend",
            duration=Decimal("2"),
            date=saturday,
            date_option_1=saturday,
            date_option_2=sunday,
            time=time(18, 0),
            location="Hall",
        )
        poll = Poll.objects.create(session=session)

        self.client.post(reverse("vote_session", args=[poll.id]), {"choice": "sat"})
        self.assertTrue(Vote.objects.filter(poll=poll, user=user, choice="sat").exists())

        self.client.post(reverse("vote_session", args=[poll.id]), {"choice": "sun"})
        self.assertTrue(Vote.objects.filter(poll=poll, user=user, choice="sun").exists())

    def test_finalize_play_day_rejects_both(self):
        saturday = timezone.localdate() + timedelta(days=5)
        sunday = timezone.localdate() + timedelta(days=6)
        session = Session.objects.create(
            name="Weekend",
            duration=Decimal("2"),
            date=saturday,
            date_option_1=saturday,
            date_option_2=sunday,
            time=time(18, 0),
            location="Hall",
        )

        resp = self.client.post(reverse("finalize_play_day", args=[session.id]), {
            "play_day": "both",
        })

        self.assertEqual(resp.status_code, 302)
        session.refresh_from_db()
        self.assertIsNone(session.final_play_day)

    def test_one_day_web_vote_keeps_yes_no_codes(self):
        user = User.objects.create_user(username="oneday", password="x")
        self.client.force_login(user)
        saturday = timezone.localdate() + timedelta(days=5)
        session = Session.objects.create(
            name="Saturday only",
            duration=Decimal("2"),
            date=saturday,
            date_option_1=saturday,
            final_play_day="sat",
            time=time(18, 0),
            location="Hall",
        )
        poll = Poll.objects.create(session=session)

        self.client.post(reverse("vote_session", args=[poll.id]), {"choice": "yes"})
        self.assertTrue(Vote.objects.filter(poll=poll, user=user, choice="yes").exists())

        self.client.post(reverse("vote_session", args=[poll.id]), {"choice": "no"})
        self.assertTrue(Vote.objects.filter(poll=poll, user=user, choice="no").exists())

    def test_one_day_poll_buttons_show_yes_no_counts(self):
        yes_user_1 = User.objects.create_user(username="yes1", password="x")
        yes_user_2 = User.objects.create_user(username="yes2", password="x")
        no_user = User.objects.create_user(username="no1", password="x")
        saturday = timezone.localdate() + timedelta(days=5)
        session = Session.objects.create(
            name="Saturday only",
            duration=Decimal("2"),
            date=saturday,
            date_option_1=saturday,
            final_play_day="sat",
            time=time(18, 0),
            location="Hall",
        )
        poll = Poll.objects.create(session=session)
        Vote.objects.create(poll=poll, user=yes_user_1, choice="yes")
        Vote.objects.create(poll=poll, user=yes_user_2, choice="yes")
        Vote.objects.create(poll=poll, user=no_user, choice="no")

        resp = self.client.get(reverse("session_detail", args=[session.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, "2 Yes")
        self.assertContains(resp, "1 No")

    def test_attendance_defaults_to_final_play_day_voters(self):
        saturday_user = User.objects.create_user(username="sat", password="x")
        sunday_user = User.objects.create_user(username="sun", password="x")
        both_user = User.objects.create_user(username="both", password="x")
        out_user = User.objects.create_user(username="out", password="x")
        session = Session.objects.create(
            name="Weekend",
            duration=Decimal("2"),
            date=timezone.localdate() - timedelta(days=1),
            date_option_1=timezone.localdate() - timedelta(days=2),
            date_option_2=timezone.localdate() - timedelta(days=1),
            final_play_day="sun",
            time=time(18, 0),
            location="Hall",
            cost=Decimal("30"),
        )
        poll = Poll.objects.create(session=session)
        Vote.objects.create(poll=poll, user=saturday_user, choice="sat")
        Vote.objects.create(poll=poll, user=sunday_user, choice="sun")
        Vote.objects.create(poll=poll, user=both_user, choice="all")
        Vote.objects.create(poll=poll, user=out_user, choice="out")

        resp = self.client.get(reverse("session_detail", args=[session.id]))

        self.assertEqual(resp.status_code, 200)
        attendance_by_user = {
            row.match_player.user.username: row.attended
            for row in Attendance.objects.select_related("match_player__user")
        }
        self.assertEqual(attendance_by_user, {
            "sun": True,
            "both": True,
        })
        self.assertEqual(SessionPlayer.objects.filter(session=session).count(), 2)
        self.assertFalse(SessionPlayer.objects.filter(session=session, user=saturday_user).exists())
        self.assertFalse(SessionPlayer.objects.filter(session=session, user=out_user).exists())

    def test_two_day_attendance_waits_for_admin_play_day(self):
        saturday_user = User.objects.create_user(username="sat_wait", password="x")
        sunday_user = User.objects.create_user(username="sun_wait", password="x")
        session = Session.objects.create(
            name="Weekend pending",
            duration=Decimal("2"),
            date=timezone.localdate() - timedelta(days=1),
            date_option_1=timezone.localdate() - timedelta(days=2),
            date_option_2=timezone.localdate() - timedelta(days=1),
            time=time(18, 0),
            location="Hall",
            cost=Decimal("30"),
        )
        poll = Poll.objects.create(session=session)
        Vote.objects.create(poll=poll, user=saturday_user, choice="sat")
        Vote.objects.create(poll=poll, user=sunday_user, choice="sun")

        resp = self.client.get(reverse("session_detail", args=[session.id]))

        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.context["attendance_waiting_for_play_day"])
        self.assertEqual(resp.context["attendance_roster"], [])
        self.assertFalse(SessionPlayer.objects.filter(session=session).exists())

    def test_scorecard_players_seed_attendance_and_chargeable_split(self):
        charge_user = User.objects.create_user(username="charge", password="x")
        guest_user = User.objects.create_user(username="guest", password="x")
        session = Session.objects.create(
            name="Scored game",
            duration=Decimal("2"),
            date=timezone.localdate() - timedelta(days=1),
            date_option_1=timezone.localdate() - timedelta(days=2),
            date_option_2=timezone.localdate() - timedelta(days=1),
            final_play_day="sun",
            time=time(18, 0),
            location="Hall",
            cost=Decimal("30"),
        )
        Poll.objects.create(session=session)
        match = Match.objects.create(session=session, name="Match 1")
        team = Team.objects.create(match=match, name="A")
        Player.objects.create(user=charge_user, team=team, role="bat")
        Player.objects.create(user=guest_user, team=team, role="bat")

        self.client.get(reverse("session_detail", args=[session.id]))
        session_players = {
            sp.user.username: sp
            for sp in SessionPlayer.objects.filter(session=session).select_related("user")
        }

        self.assertEqual(set(session_players), {"charge", "guest"})

        resp = self.client.post(reverse("session_attendance_detail", args=[session.id]), {
            "present": [str(session_players["charge"].id), str(session_players["guest"].id)],
            "chargeable": [str(session_players["charge"].id)],
        })

        self.assertEqual(resp.status_code, 302)
        session.refresh_from_db()
        self.assertTrue(session.attendance_confirmed)
        self.assertEqual(session.cost_per_person, Decimal("30.00"))
        self.assertTrue(Payment.objects.filter(
            session=session,
            user=charge_user,
            amount=Decimal("30.00"),
            status="pending",
        ).exists())
        self.assertFalse(Payment.objects.filter(session=session, user=guest_user).exists())
        self.assertFalse(Attendance.objects.get(match_player=session_players["charge"]).cost_exempt)
        self.assertTrue(Attendance.objects.get(match_player=session_players["guest"]).cost_exempt)
