"""Seed a fully-scored test match (and session) into the local DB so the new
award features — Orange Cap, Purple Cap, Player of the Match / Session — have
real ball-by-ball data to render.

    python manage.py seed_test_match                 # 1 match, 6 overs, 8-a-side
    python manage.py seed_test_match --matches 2     # 2 matches in the session
    python manage.py seed_test_match --overs 5 --seed 7

Everything derives from the Delivery ledger, so this drives the real scoring
engine (record_delivery) rather than writing cached totals directly.
"""
import random
from datetime import time

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.sessions.models import Session
from apps.matches.models import Match, Team, Player, Delivery
from apps.matches import scoring

User = get_user_model()

FIRST_NAMES = [
    'Arjun', 'Rohit', 'Virat', 'Kane', 'Steve', 'Joe', 'Babar', 'David',
    'Quinton', 'Jos', 'Ben', 'Pat', 'Mitchell', 'Trent', 'Jasprit', 'Rashid',
    'Shakib', 'Hardik', 'Ravindra', 'Glenn',
]
TEAM_NAMES = [('Strikers', 'Titans'), ('Warriors', 'Royals'), ('Kings', 'Chargers')]


class Command(BaseCommand):
    help = 'Seed a scored test match + session with random ball-by-ball data.'

    def add_arguments(self, parser):
        parser.add_argument('--matches', type=int, default=1, help='matches in the session')
        parser.add_argument('--overs', type=int, default=6, help='overs per innings')
        parser.add_argument('--per-side', type=int, default=8, help='players per team')
        parser.add_argument('--seed', type=int, default=None, help='RNG seed for reproducibility')

    def handle(self, *args, **opts):
        rng = random.Random(opts['seed'])
        overs = max(1, opts['overs'])
        per_side = max(2, opts['per_side'])
        n_matches = max(1, opts['matches'])
        needed = per_side * 2

        users = self._ensure_users(needed, rng)

        session = Session.objects.create(
            name=f"Test Session {Session.objects.count() + 1}",
            cost=0, duration=2, date=timezone.now().date(),
            time=time(18, 0), location='Local Ground',
            attendance_confirmed=True,
        )
        self.stdout.write(self.style.SUCCESS(f"Created session #{session.id}: {session.name}"))

        for m in range(n_matches):
            # Shuffle the roster per match so caps / awards vary between matches.
            rng.shuffle(users)
            self._seed_match(session, users[:needed], per_side, overs, m, rng)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone. Open: /session/{session.id}/  ->  view each scorecard for the awards."
        ))

    # ── setup ──────────────────────────────────────────────────────────────
    def _ensure_users(self, needed, rng):
        users = list(User.objects.filter(is_active=True).order_by('id'))
        roles = ['batsman', 'bowler', 'allrounder']
        i = 0
        while len(users) < needed:
            i += 1
            uname = f"testplayer{i}"
            if User.objects.filter(username=uname).exists():
                continue
            name = rng.choice(FIRST_NAMES)
            u = User.objects.create(
                username=uname, first_name=name, role=rng.choice(roles),
                batting_rating=round(rng.uniform(1, 5), 1),
                bowling_rating=round(rng.uniform(1, 5), 1),
                fielding_rating=round(rng.uniform(1, 5), 1),
            )
            u.set_password('test1234')
            u.save()
            users.append(u)
        if len(users) > needed:
            self.stdout.write(f"Using {needed} of {len(users)} existing users.")
        return users

    def _seed_match(self, session, roster, per_side, overs, index, rng):
        names = TEAM_NAMES[index % len(TEAM_NAMES)]
        match = Match.objects.create(
            session=session, name=f"Match {index + 1}", overs_limit=overs,
        )
        team_a = Team.objects.create(match=match, name=names[0])
        team_b = Team.objects.create(match=match, name=names[1])

        a_users, b_users = roster[:per_side], roster[per_side:per_side * 2]
        a_players = [Player.objects.create(team=team_a, user=u, role=u.role or 'allrounder') for u in a_users]
        b_players = [Player.objects.create(team=team_b, user=u, role=u.role or 'allrounder') for u in b_users]

        # Toss + first innings.
        match.toss_winner = team_a
        match.toss_decision = 'bat'
        match.save(update_fields=['toss_winner', 'toss_decision'])

        inn1 = scoring.start_innings(
            match, number=1, batting_team=team_a, bowling_team=team_b,
            striker=a_players[0], non_striker=a_players[1], bowler=b_players[0],
        )
        r1 = self._simulate(inn1, a_players, b_players, overs, rng, target=None)
        inn1.is_closed = True
        inn1.save(update_fields=['is_closed'])

        inn2 = scoring.start_innings(
            match, number=2, batting_team=team_b, bowling_team=team_a,
            striker=b_players[0], non_striker=b_players[1], bowler=a_players[0],
        )
        self._simulate(inn2, b_players, a_players, overs, rng, target=r1 + 1)
        inn2.is_closed = True
        inn2.save(update_fields=['is_closed'])

        winner = scoring.finalize_match_result(match)
        result = scoring.result_line(match) or 'Tied'
        self.stdout.write(f"  {match.name}: {result}")

    # ── simulation ─────────────────────────────────────────────────────────
    def _simulate(self, innings, batting, bowling, overs, rng, target):
        """Play an innings ball-by-ball. Returns the total runs scored."""
        max_wickets = len(batting) - 1
        striker, non_striker = batting[0], batting[1]
        next_batter = 2
        wickets = total_runs = legal_total = 0
        prev_bowler = None

        for over in range(overs):
            if wickets >= max_wickets:
                break
            if target is not None and total_runs >= target:
                break
            choices = [b for b in bowling if b is not prev_bowler] or bowling
            bowler = rng.choice(choices)
            balls = 0
            while balls < 6:
                if wickets >= max_wickets:
                    break
                if target is not None and total_runs >= target:
                    break

                roll = rng.random()
                runs = extra_runs = 0
                extra_type = Delivery.EXTRA_NONE
                is_wicket = False
                dismissal = ''
                out_player = fielder = None

                if roll < 0.05:          # wide
                    extra_type, extra_runs = Delivery.EXTRA_WIDE, 1
                elif roll < 0.08:        # no-ball (+ runs off the bat)
                    extra_type, extra_runs = Delivery.EXTRA_NOBALL, 1
                    runs = rng.choice([0, 1, 1, 2, 4])
                elif roll < 0.15:        # wicket
                    is_wicket = True
                    dismissal = rng.choice(['bowled', 'caught', 'caught', 'lbw', 'runout', 'stumped'])
                    out_player = striker
                    if dismissal in ('caught', 'runout', 'stumped'):
                        fcands = [f for f in bowling if f is not bowler] or bowling
                        fielder = rng.choice(fcands)
                else:                    # runs (occasionally as byes/leg-byes)
                    runs = rng.choices([0, 1, 2, 3, 4, 6], weights=[28, 30, 12, 3, 17, 10])[0]
                    if runs and rng.random() < 0.06:
                        extra_type = rng.choice([Delivery.EXTRA_BYE, Delivery.EXTRA_LEGBYE])
                        extra_runs, runs = runs, 0

                scoring.record_delivery(
                    innings, striker=striker, non_striker=non_striker, bowler=bowler,
                    runs_off_bat=runs, extra_type=extra_type, extra_runs=extra_runs,
                    is_wicket=is_wicket, dismissal_type=dismissal,
                    out_player=out_player, fielder=fielder,
                )

                total_runs += runs + extra_runs
                is_legal = extra_type not in (Delivery.EXTRA_WIDE, Delivery.EXTRA_NOBALL)
                if is_legal:
                    balls += 1
                    legal_total += 1

                if is_wicket:
                    wickets += 1
                    if next_batter < len(batting):
                        striker = batting[next_batter]
                        next_batter += 1
                    else:
                        break
                else:
                    ran = runs + (extra_runs if extra_type in (Delivery.EXTRA_BYE, Delivery.EXTRA_LEGBYE) else 0)
                    if ran % 2 == 1:
                        striker, non_striker = non_striker, striker

            striker, non_striker = non_striker, striker  # end-of-over swap
            prev_bowler = bowler

        return total_runs
