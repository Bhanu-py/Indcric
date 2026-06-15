"""Tests for the staff match-delete guard (issue #39).

A played match (with a saved ball-by-ball scorecard) was wiped by an accidental
one-tap delete. delete_match_view now refuses to destroy a scored match unless
the staff re-types the match name in a `confirm_name` field.
"""
from datetime import date, time
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from apps.matches.models import Delivery, Innings, Match, Player, Team
from apps.sessions.models import Session

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
