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
        sunday = timezone.localdate() + timedelta(days=4)

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
        self.assertEqual(session.poll.question, "Can you play on Sunday?")

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
        Vote.objects.create(poll=poll, user=saturday_user, choice="yes")
        Vote.objects.create(poll=poll, user=sunday_user, choice="no")
        Vote.objects.create(poll=poll, user=both_user, choice="all")
        Vote.objects.create(poll=poll, user=out_user, choice="out")

        resp = self.client.get(reverse("session_detail", args=[session.id]))

        self.assertEqual(resp.status_code, 200)
        attendance_by_user = {
            row.match_player.user.username: row.attended
            for row in Attendance.objects.select_related("match_player__user")
        }
        self.assertEqual(attendance_by_user, {
            "sat": False,
            "sun": True,
            "both": True,
        })
        self.assertEqual(SessionPlayer.objects.filter(session=session).count(), 3)
        self.assertFalse(SessionPlayer.objects.filter(session=session, user=out_user).exists())
