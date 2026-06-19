from django.contrib.contenttypes.fields import GenericRelation
from django.db import models



class Match(models.Model):
    # Deleting a match removes its activity-feed rows (e.g. the result entry).
    feed_events = GenericRelation('notifications.ActivityEvent')
    # String ref avoids circular import: matches → sessions
    session = models.ForeignKey(
        'cric_sessions.Session',
        on_delete=models.CASCADE,
        related_name='matches',
        null=True,
    )
    name = models.CharField(max_length=100)
    winner = models.ForeignKey(
        'Team',
        on_delete=models.SET_NULL,
        related_name='won_matches',
        null=True,
        blank=True,
    )
    # Fixed overs cap per innings for ball-by-ball scoring; null until scoring starts.
    overs_limit = models.PositiveSmallIntegerField(null=True, blank=True)
    # Toss result, set at innings-1 setup.
    toss_winner = models.ForeignKey(
        'Team', on_delete=models.SET_NULL, related_name='+', null=True, blank=True
    )
    toss_decision = models.CharField(max_length=4, blank=True)  # 'bat' | 'bowl'

    @property
    def is_completed(self):
        """Both innings scored and closed — a result (win or tie) stands."""
        innings = list(self.innings.all())
        return len(innings) >= 2 and all(i.is_closed for i in innings)

    @property
    def is_tied(self):
        """Completed with level scores: winner stays NULL, unlike an unfinished
        match where winner is also NULL — templates need the distinction."""
        return self.winner_id is None and self.is_completed

    def __str__(self):
        return f"{self.name} in {self.session.name}"
from django.db import connections
from decimal import Decimal

class Session(models.Model):
    # assuming cric_sessions.Session already exists, add this for previous session
    matches = models.ManyToManyField('Match', related_name='previous_sessions')

    def get_previous_session(self):
        try:
            return self.matches.filter(is_completed=True)[0]
        except IndexError:
            return None

class Team(models.Model):
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='teams')
    name = models.CharField(max_length=100)
    captain = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='captained_teams',
    )
    runs = models.PositiveIntegerField(default=0)
    wickets = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Player(models.Model):
    user = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='players')
    paid = models.BooleanField(default=False)
    role = models.CharField(max_length=20)

    class Meta:
        unique_together = [('user', 'team')]

    def __str__(self):
        return self.user.username


class Innings(models.Model):
    """One team's batting innings within a Match.

    A match has up to two innings (number 1 and 2). Scores aren't stored here —
    they derive from the innings' Delivery rows (see apps/matches/scoring.py).
    """
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='innings')
    number = models.PositiveSmallIntegerField(default=1)  # 1 or 2
    batting_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='batting_innings'
    )
    bowling_team = models.ForeignKey(
        Team, on_delete=models.CASCADE, related_name='bowling_innings'
    )
    is_closed = models.BooleanField(default=False)  # all out / overs done / manual end
    # Last man stands: when the would-be-final wicket falls the scorer may let
    # the surviving batter continue alone; the innings then runs until every
    # batter is out instead of ending one wicket early.
    single_batting = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Live scorer working-state: who faces / bowls the NEXT ball. Mutable pointers
    # (the Delivery ledger stays immutable). current_striker is cleared after a
    # wicket until the scorer picks the incoming batter; current_bowler is cleared
    # at the end of an over until a new bowler is chosen.
    current_striker = models.ForeignKey(
        Player, on_delete=models.SET_NULL, related_name='+', null=True, blank=True
    )
    current_non_striker = models.ForeignKey(
        Player, on_delete=models.SET_NULL, related_name='+', null=True, blank=True
    )
    current_bowler = models.ForeignKey(
        Player, on_delete=models.SET_NULL, related_name='+', null=True, blank=True
    )

    class Meta:
        unique_together = [('match', 'number')]
        ordering = ['match', 'number']

    def __str__(self):
        return f"{self.match.name} — innings {self.number}"


class Retirement(models.Model):
    """A batter leaving the crease without being dismissed (retired hurt).

    Not a ball and not a wicket, so it can't live in the Delivery ledger —
    but the batting card needs the label and the console must vacate the
    right end. `at_sequence` anchors it in the ledger: the player counts as
    "returned" once any later delivery shows them back at the crease, and
    they stay eligible to resume batting while an end is vacant.
    """
    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='retirements')
    player = models.ForeignKey(Player, on_delete=models.CASCADE, related_name='+')
    at_sequence = models.PositiveIntegerField(default=0)  # last ledger sequence when retired
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.player} retired hurt — {self.innings}"


class Delivery(models.Model):
    """One ball. Immutable append-only ledger — the source of truth for scoring.

    Team totals, overs, and per-player cards all derive by aggregating these
    rows, mirroring the Wallet ledger (sum of rows = balance). Undo = delete the
    highest `sequence`; corrections re-derive rather than mutate cached scores.
    """
    EXTRA_NONE = 'none'
    EXTRA_WIDE = 'wide'
    EXTRA_NOBALL = 'noball'
    EXTRA_BYE = 'bye'
    EXTRA_LEGBYE = 'legbye'
    EXTRA_CHOICES = [
        (EXTRA_NONE, 'None'),
        (EXTRA_WIDE, 'Wide'),
        (EXTRA_NOBALL, 'No ball'),
        (EXTRA_BYE, 'Bye'),
        (EXTRA_LEGBYE, 'Leg bye'),
    ]
    DISMISSAL_CHOICES = [
        ('bowled', 'Bowled'),
        ('caught', 'Caught'),
        ('lbw', 'LBW'),
        ('runout', 'Run out'),
        ('stumped', 'Stumped'),
        ('hitwicket', 'Hit wicket'),
        ('other', 'Other'),
    ]
    # Dismissals the bowler is credited with (run-out is not the bowler's wicket).
    BOWLER_DISMISSALS = {'bowled', 'caught', 'lbw', 'stumped', 'hitwicket'}

    innings = models.ForeignKey(Innings, on_delete=models.CASCADE, related_name='deliveries')
    sequence = models.PositiveIntegerField()  # order within innings; undo = delete max
    # Client-generated id so a retried/replayed POST is deduped (online retry now,
    # offline replay later). Blank for rows created server-side (e.g. admin).
    client_uuid = models.CharField(max_length=64, blank=True, default='')
    over_number = models.PositiveSmallIntegerField(default=0)   # 0-based
    ball_in_over = models.PositiveSmallIntegerField(default=0)  # legal-ball index 1..6

    striker = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='+')
    non_striker = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='+', null=True, blank=True
    )
    bowler = models.ForeignKey(Player, on_delete=models.PROTECT, related_name='+')

    runs_off_bat = models.PositiveSmallIntegerField(default=0)
    extra_type = models.CharField(max_length=10, choices=EXTRA_CHOICES, default=EXTRA_NONE)
    extra_runs = models.PositiveSmallIntegerField(default=0)

    is_wicket = models.BooleanField(default=False)
    dismissal_type = models.CharField(max_length=12, choices=DISMISSAL_CHOICES, blank=True)
    out_player = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='+', null=True, blank=True
    )
    fielder = models.ForeignKey(
        Player, on_delete=models.PROTECT, related_name='+', null=True, blank=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sequence']
        constraints = [
            models.UniqueConstraint(
                fields=['innings', 'sequence'], name='uniq_innings_sequence'
            ),
            models.UniqueConstraint(
                fields=['innings', 'client_uuid'],
                condition=~models.Q(client_uuid=''),
                name='uniq_innings_client_uuid',
            ),
        ]

    @property
    def is_legal(self):
        """A legal ball counts toward the over; wides and no-balls don't."""
        return self.extra_type not in (self.EXTRA_WIDE, self.EXTRA_NOBALL)

    @property
    def total_runs(self):
        """Runs added to the team total for this ball."""
        return self.runs_off_bat + self.extra_runs

    @property
    def runs_conceded(self):
        """Runs charged to the bowler — byes and leg-byes are not."""
        penalty = self.extra_runs if self.extra_type in (self.EXTRA_WIDE, self.EXTRA_NOBALL) else 0
        return self.runs_off_bat + penalty

    def __str__(self):
        return f"{self.innings} — ball {self.sequence}"
