from datetime import time as dtime
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from apps.sessions.models import Session
from .models import Match, Team, Player, Innings, Delivery
from . import scoring

User = get_user_model()


class MatchFixtureMixin:
    """A 3-a-side match with innings 1 ready to score (team A batting)."""
    def setUp(self):
        self.session = Session.objects.create(
            name="Test", cost=Decimal('0'), duration=Decimal('3'),
            date=timezone.now().date(), time=dtime(18, 0), location="GUSB",
        )
        self.match = Match.objects.create(session=self.session, name="Match 1", overs_limit=2)
        self.team_a = Team.objects.create(match=self.match, name="A")
        self.team_b = Team.objects.create(match=self.match, name="B")
        self.a = [self._player(self.team_a, f"a{i}") for i in range(1, 4)]
        self.b = [self._player(self.team_b, f"b{i}") for i in range(1, 4)]
        self.inn = Innings.objects.create(
            match=self.match, number=1,
            batting_team=self.team_a, bowling_team=self.team_b,
        )

    def _player(self, team, username):
        user = User.objects.create_user(username=username, password="x")
        return Player.objects.create(user=user, team=team, role="batsman")


class ScoringEngineTests(MatchFixtureMixin, TestCase):
    def _seven_ball_over(self):
        """Records the hand-computed scenario used by several tests."""
        a1, a2, a3 = self.a
        b1 = self.b[0]
        rd = scoring.record_delivery
        rd(self.inn, striker=a1, non_striker=a2, bowler=b1, runs_off_bat=1)            # 1
        rd(self.inn, striker=a2, non_striker=a1, bowler=b1, runs_off_bat=4)            # 2
        rd(self.inn, striker=a2, non_striker=a1, bowler=b1, extra_type='wide', extra_runs=1)  # 3
        rd(self.inn, striker=a2, non_striker=a1, bowler=b1, runs_off_bat=6)            # 4
        rd(self.inn, striker=a2, non_striker=a1, bowler=b1, extra_type='bye', extra_runs=2)   # 5
        rd(self.inn, striker=a2, non_striker=a1, bowler=b1, is_wicket=True,
           dismissal_type='bowled', out_player=a2)                                     # 6
        rd(self.inn, striker=a3, non_striker=a1, bowler=b1, runs_off_bat=2)            # 7

    def test_innings_aggregation(self):
        self._seven_ball_over()
        score = scoring.innings_score(self.inn)
        # runs: 1+4+1(wide)+6+2(bye)+0+2 = 16 ; extras 1+2 = 3 ; 1 wicket ; 6 legal
        self.assertEqual(score['runs'], 16)
        self.assertEqual(score['extras'], 3)
        self.assertEqual(score['wickets'], 1)
        self.assertEqual(score['legal_balls'], 6)
        self.assertEqual(score['overs'], "1.0")

    def test_team_cache_synced(self):
        self._seven_ball_over()
        self.team_a.refresh_from_db()
        self.assertEqual(self.team_a.runs, 16)
        self.assertEqual(self.team_a.wickets, 1)

    def test_batting_card(self):
        self._seven_ball_over()
        card = {row['player'].user.username: row for row in scoring.batting_card(self.inn)}
        self.assertEqual(card['a1']['runs'], 1)
        self.assertEqual(card['a1']['balls'], 1)
        # a2: 4 + 6 = 10 off 4 balls faced (wide excluded), 1 four, 1 six, bowled
        self.assertEqual(card['a2']['runs'], 10)
        self.assertEqual(card['a2']['balls'], 4)
        self.assertEqual(card['a2']['fours'], 1)
        self.assertEqual(card['a2']['sixes'], 1)
        self.assertTrue(card['a2']['out'])
        self.assertEqual(card['a2']['how_out'], "bowled b1")
        self.assertEqual(card['a2']['strike_rate'], 250.0)
        self.assertEqual(card['a3']['runs'], 2)
        self.assertFalse(card['a3']['out'])

    def test_bowling_card_excludes_byes_and_runouts(self):
        self._seven_ball_over()
        b1card = scoring.bowling_card(self.inn)[0]
        # conceded: 1+4+1(wide)+6+0(bye not charged)+0+2 = 14 ; 6 legal ; 1 wkt (bowled)
        self.assertEqual(b1card['runs'], 14)
        self.assertEqual(b1card['overs'], "1.0")
        self.assertEqual(b1card['wickets'], 1)
        self.assertEqual(b1card['economy'], 14.0)

    def test_runout_not_credited_to_bowler(self):
        a1, a2, _ = self.a
        b1 = self.b[0]
        scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1,
                                is_wicket=True, dismissal_type='runout', out_player=a1)
        self.assertEqual(scoring.bowling_card(self.inn)[0]['wickets'], 0)
        self.assertEqual(scoring.innings_score(self.inn)['wickets'], 1)

    def test_runout_counts_completed_runs(self):
        # Out going for the 2nd: 1 completed run counts to the striker and total.
        a1, a2, _ = self.a
        b1 = self.b[0]
        scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1,
                                runs_off_bat=1, is_wicket=True,
                                dismissal_type='runout', out_player=a1)
        score = scoring.innings_score(self.inn)
        self.assertEqual(score['runs'], 1)
        self.assertEqual(score['wickets'], 1)
        card = {row['player'].user.username: row for row in scoring.batting_card(self.inn)}
        self.assertEqual(card['a1']['runs'], 1)
        self.assertTrue(card['a1']['out'])

    def test_complete_on_overs_limit(self):
        self.match.overs_limit = 1  # one over
        self.match.save()
        a1, a2 = self.a[0], self.a[1]
        b1 = self.b[0]
        self.assertFalse(scoring.is_innings_complete(self.inn))
        for _ in range(6):
            scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1, runs_off_bat=0)
        self.assertTrue(scoring.is_innings_complete(self.inn))

    def test_complete_on_all_out(self):
        # roster of 3 → all out at 2 wickets
        a1, a2, a3 = self.a
        b1 = self.b[0]
        scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1,
                                is_wicket=True, dismissal_type='bowled', out_player=a1)
        self.assertFalse(scoring.is_innings_complete(self.inn))
        scoring.record_delivery(self.inn, striker=a3, non_striker=a2, bowler=b1,
                                is_wicket=True, dismissal_type='bowled', out_player=a3)
        self.assertTrue(scoring.is_innings_complete(self.inn))

    def test_wide_does_not_advance_over(self):
        a1, a2 = self.a[0], self.a[1]
        b1 = self.b[0]
        for _ in range(3):
            scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1,
                                    extra_type='wide', extra_runs=1)
        # 3 wides → 0 legal balls, still over 0.0
        self.assertEqual(scoring.innings_score(self.inn)['overs'], "0.0")
        self.assertEqual(scoring.innings_score(self.inn)['runs'], 3)

    def test_idempotent_client_uuid(self):
        a1, a2 = self.a[0], self.a[1]
        b1 = self.b[0]
        d1 = scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1,
                                     runs_off_bat=4, client_uuid='ball-xyz')
        d2 = scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1,
                                     runs_off_bat=4, client_uuid='ball-xyz')
        self.assertEqual(d1.id, d2.id)
        self.assertEqual(self.inn.deliveries.count(), 1)

    def test_undo_last(self):
        self._seven_ball_over()
        before = self.inn.deliveries.count()
        scoring.undo_last(self.inn)
        self.assertEqual(self.inn.deliveries.count(), before - 1)
        self.team_a.refresh_from_db()
        self.assertEqual(self.team_a.runs, 14)  # 16 minus the last 2-run ball

    def test_strike_rotation_suggestion(self):
        a1, a2 = self.a[0], self.a[1]
        b1 = self.b[0]
        scoring.record_delivery(self.inn, striker=a1, non_striker=a2, bowler=b1, runs_off_bat=1)
        striker, non_striker = scoring.on_strike_for_next(self.inn)
        self.assertEqual(striker, a2)      # single → batters crossed
        self.assertEqual(non_striker, a1)

    def test_tied_match_is_completed_not_live(self):
        scoring.record_delivery(self.inn, striker=self.a[0], non_striker=self.a[1],
                                bowler=self.b[0], runs_off_bat=4)
        self.inn.is_closed = True
        self.inn.save()
        inn2 = Innings.objects.create(
            match=self.match, number=2,
            batting_team=self.team_b, bowling_team=self.team_a,
        )
        scoring.record_delivery(inn2, striker=self.b[0], non_striker=self.b[1],
                                bowler=self.a[0], runs_off_bat=4)
        inn2.is_closed = True
        inn2.save()
        self.assertIsNone(scoring.finalize_match_result(self.match))
        self.match.refresh_from_db()
        self.assertTrue(self.match.is_completed)
        self.assertTrue(self.match.is_tied)
        self.assertEqual(scoring.result_line(self.match), "Match tied")

    def test_finalize_match_result(self):
        # Innings 1 (A) = 16
        self._seven_ball_over()
        self.inn.is_closed = True
        self.inn.save()
        inn2 = Innings.objects.create(
            match=self.match, number=2,
            batting_team=self.team_b, bowling_team=self.team_a,
        )
        scoring.record_delivery(inn2, striker=self.b[0], non_striker=self.b[1],
                                bowler=self.a[0], runs_off_bat=4)  # B = 4
        inn2.is_closed = True
        inn2.save()
        winner = scoring.finalize_match_result(self.match)
        self.assertEqual(winner, self.team_a)
        self.match.refresh_from_db()
        self.assertEqual(self.match.winner, self.team_a)


class ScoreBallViewTests(MatchFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_user(username="staff", password="x", is_staff=True)
        self.inn.current_striker = self.a[0]
        self.inn.current_non_striker = self.a[1]
        self.inn.current_bowler = self.b[0]
        self.inn.save()
        self.client.force_login(self.staff)

    def _post(self, data):
        return self.client.post(reverse('score_ball', args=[self.inn.id]), data)

    def test_runout_posts_completed_runs(self):
        self._post({
            'wicket': '1', 'dismissal': 'runout', 'fielder': self.b[1].id,
            'wicket_runs': '1', 'out_end': 'nonstriker', 'uuid': 'ball-1',
        })
        d = self.inn.deliveries.get()
        self.assertTrue(d.is_wicket)
        self.assertEqual(d.runs_off_bat, 1)
        self.assertEqual(d.out_player, self.a[1])
        self.assertEqual(d.fielder, self.b[1])

    def test_nonstriker_runout_prompts_for_replacement(self):
        from .views import _console_context
        self._post({
            'wicket': '1', 'dismissal': 'runout', 'fielder': self.b[1].id,
            'wicket_runs': '0', 'out_end': 'nonstriker', 'uuid': 'ball-2',
        })
        self.inn.refresh_from_db()
        self.assertIsNone(self.inn.current_non_striker)
        ctx = _console_context(self.inn)
        self.assertTrue(ctx['need_batter'])
        self.assertEqual(ctx['vacant_end'], 'nonstriker')
        # only the bench batter is offered: a1 is at the crease, a2 is out
        self.assertEqual([p.id for p in ctx['available_batters']], [self.a[2].id])


class RetiredHurtTests(MatchFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.inn.current_striker = self.a[0]
        self.inn.current_non_striker = self.a[1]
        self.inn.current_bowler = self.b[0]
        self.inn.save()

    def _ball(self, runs=0, striker=None, non_striker=None):
        scoring.record_delivery(self.inn, striker=striker or self.a[0],
                                non_striker=non_striker or self.a[1],
                                bowler=self.b[0], runs_off_bat=runs)

    def test_retire_vacates_end_without_a_wicket(self):
        self._ball()
        scoring.retire_batter(self.inn, self.a[0])
        self.inn.refresh_from_db()
        self.assertIsNone(self.inn.current_striker)
        self.assertEqual(self.inn.current_non_striker, self.a[1])
        self.assertEqual(scoring.innings_score(self.inn)['wickets'], 0)
        card = {r['player'].user.username: r for r in scoring.batting_card(self.inn)}
        self.assertEqual(card['a1']['how_out'], 'retired hurt')
        self.assertFalse(card['a1']['out'])

    def test_resuming_batter_clears_the_label(self):
        self._ball()
        scoring.retire_batter(self.inn, self.a[0])
        self.assertEqual(scoring.active_retired_ids(self.inn), {self.a[0].id})
        # a1 returns to the crease and faces another ball
        self._ball()
        self.assertEqual(scoring.active_retired_ids(self.inn), set())
        card = {r['player'].user.username: r for r in scoring.batting_card(self.inn)}
        self.assertEqual(card['a1']['how_out'], '')

    def test_undo_does_not_restore_retired_batter(self):
        self._ball()                                  # ball 1: a1 & a2
        scoring.retire_batter(self.inn, self.a[1])    # a2 retires hurt
        self.inn.refresh_from_db()
        self.inn.current_non_striker = self.a[2]      # a3 comes in
        self.inn.save()
        self._ball(non_striker=self.a[2])             # ball 2: a1 & a3
        scoring.undo_last(self.inn)
        scoring.advance_after_delivery(self.inn)
        self.inn.refresh_from_db()
        # Rewinding to ball 1 must not put the retired a2 back at the crease.
        self.assertIsNone(self.inn.current_non_striker)


class SingleBattingTests(MatchFixtureMixin, TestCase):
    """Last man stands: roster of 3 normally ends the innings at 2 wickets."""
    def setUp(self):
        super().setUp()
        self.inn.current_striker = self.a[0]
        self.inn.current_non_striker = self.a[1]
        self.inn.current_bowler = self.b[0]
        self.inn.save()
        self.staff = User.objects.create_user(username="staff", password="x", is_staff=True)
        self.client.force_login(self.staff)

    def _two_down(self):
        scoring.score_ball(self.inn, is_wicket=True, dismissal_type='bowled')  # a1 out
        self.inn.current_striker = self.a[2]
        self.inn.save()
        scoring.score_ball(self.inn, is_wicket=True, dismissal_type='bowled')  # a3 out

    def test_offer_appears_then_innings_continues_until_all_out(self):
        from .views import _console_context
        self._two_down()
        self.inn.refresh_from_db()
        self.assertTrue(scoring.is_innings_complete(self.inn))
        self.assertTrue(_console_context(self.inn)['can_single_bat'])

        self.client.post(reverse('score_single_batting', args=[self.inn.id]))
        self.inn.refresh_from_db()
        self.assertTrue(self.inn.single_batting)
        self.assertEqual(self.inn.current_striker, self.a[1])  # survivor takes strike
        self.assertIsNone(self.inn.current_non_striker)
        self.assertFalse(scoring.is_innings_complete(self.inn))
        ctx = _console_context(self.inn)
        self.assertFalse(ctx['need_batter'])  # empty non-striker end is normal now

        scoring.score_ball(self.inn, is_wicket=True, dismissal_type='bowled')  # a2 out
        self.assertTrue(scoring.is_innings_complete(self.inn))
        self.assertEqual(scoring.innings_score(self.inn)['wickets'], 3)

    def test_lone_batter_keeps_strike(self):
        self._two_down()
        self.client.post(reverse('score_single_batting', args=[self.inn.id]))
        self.inn.refresh_from_db()
        scoring.score_ball(self.inn, runs_off_bat=1)  # single would normally rotate
        self.inn.refresh_from_db()
        self.assertEqual(self.inn.current_striker, self.a[1])
        self.assertIsNone(self.inn.current_non_striker)

    def test_no_offer_when_overs_are_done(self):
        from .views import _console_context
        self.match.overs_limit = 1
        self.match.save()
        for _ in range(5):
            scoring.score_ball(self.inn, runs_off_bat=0)
        scoring.score_ball(self.inn, is_wicket=True, dismissal_type='bowled')
        self.inn.refresh_from_db()
        # one wicket down but the over allowance is finished — no continue offer
        self.assertTrue(scoring.is_innings_complete(self.inn))
        self.assertFalse(_console_context(self.inn)['can_single_bat'])


class ScoreAdjustViewTests(MatchFixtureMixin, TestCase):
    def setUp(self):
        super().setUp()
        self.staff = User.objects.create_user(username="staff", password="x", is_staff=True)
        self.inn.current_striker = self.a[0]
        self.inn.current_non_striker = self.a[1]
        self.inn.current_bowler = self.b[0]
        self.inn.save()
        self.client.force_login(self.staff)

    def _dot_ball(self):
        scoring.record_delivery(self.inn, striker=self.a[0], non_striker=self.a[1],
                                bowler=self.b[0], runs_off_bat=0)

    def test_swap_strike(self):
        self.client.post(reverse('score_swap_strike', args=[self.inn.id]))
        self.inn.refresh_from_db()
        self.assertEqual(self.inn.current_striker, self.a[1])
        self.assertEqual(self.inn.current_non_striker, self.a[0])

    def test_set_nonstriker_to_current_striker_swaps(self):
        self.client.post(reverse('score_set_batter', args=[self.inn.id]),
                         {'player': self.a[0].id, 'end': 'nonstriker'})
        self.inn.refresh_from_db()
        self.assertEqual(self.inn.current_striker, self.a[1])
        self.assertEqual(self.inn.current_non_striker, self.a[0])

    def test_change_bowler_clears_pointer(self):
        self.client.post(reverse('score_change_bowler', args=[self.inn.id]))
        self.inn.refresh_from_db()
        self.assertIsNone(self.inn.current_bowler)

    def test_midover_bowler_picker_has_no_exclusion(self):
        from .views import _console_context
        self._dot_ball()  # 0.1 ov — mid-over
        self.inn.current_bowler = None
        ids = {p.id for p in _console_context(self.inn)['available_bowlers']}
        self.assertIn(self.b[0].id, ids)  # mis-tap recovery: same bowler may resume

    def test_over_boundary_excludes_previous_bowler(self):
        from .views import _console_context
        for _ in range(6):
            self._dot_ball()
        ids = {p.id for p in _console_context(self.inn)['available_bowlers']}
        self.assertNotIn(self.b[0].id, ids)  # no consecutive overs

    def test_reopen_scoring_reopens_latest_and_clears_winner(self):
        self._dot_ball()
        self.inn.is_closed = True
        self.inn.save()
        inn2 = Innings.objects.create(
            match=self.match, number=2,
            batting_team=self.team_b, bowling_team=self.team_a,
        )
        scoring.record_delivery(inn2, striker=self.b[0], non_striker=self.b[1],
                                bowler=self.a[0], runs_off_bat=4)
        inn2.is_closed = True
        inn2.save()
        scoring.finalize_match_result(self.match)
        self.match.refresh_from_db()
        self.assertEqual(self.match.winner, self.team_b)

        self.client.post(reverse('reopen_scoring', args=[self.match.id]))
        inn2.refresh_from_db()
        self.inn.refresh_from_db()
        self.match.refresh_from_db()
        self.assertFalse(inn2.is_closed)      # latest innings reopened
        self.assertTrue(self.inn.is_closed)   # innings 1 untouched — target can't shift
        self.assertIsNone(self.match.winner)  # result cleared until re-finished

    def test_set_overs_floored_at_overs_begun(self):
        for _ in range(7):  # 1.1 ov
            self._dot_ball()
        self.client.post(reverse('score_set_overs', args=[self.inn.id]), {'overs': '1'})
        self.match.refresh_from_db()
        self.assertEqual(self.match.overs_limit, 2)
        self.client.post(reverse('score_set_overs', args=[self.inn.id]), {'overs': '5'})
        self.match.refresh_from_db()
        self.assertEqual(self.match.overs_limit, 5)
