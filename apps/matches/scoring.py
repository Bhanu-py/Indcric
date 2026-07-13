"""Scoring engine for ball-by-ball match data.

Everything derives from the immutable Delivery ledger (sum of rows = score),
mirroring the Wallet ledger pattern. This module has two halves:

  * Derivation (pure reads): innings_score, batting_card, bowling_card,
    fall_of_wickets, this_over, on_strike_for_next, is_innings_complete.
  * Writes (transactional): record_delivery, undo_last, sync_team_cache,
    finalize_match_result — append/remove a ball and keep the Team runs/wickets
    cache + Match.winner in step.

Cricket conventions used here:
  * Legal ball = not a wide/no-ball; only legal balls advance the over.
  * Bowler is charged runs off the bat + wide/no-ball penalties, but NOT
    byes/leg-byes. Bowler is credited all dismissals except run-out.
  * Balls faced by a batter exclude wides (no-balls count as faced).
"""
from django.db import transaction

from .models import Innings, Delivery, Match, Player, Retirement


# ── Derivation (pure reads) ──────────────────────────────────────────────────

def _deliveries(innings):
    # select_related the player→user chain so name access in the cards is cheap.
    return list(
        innings.deliveries.select_related(
            'striker__user', 'non_striker__user', 'bowler__user',
            'out_player__user', 'fielder__user',
        )
    )  # ordering = ['sequence']


def _name(player):
    if not player:
        return ''
    return player.user.first_name or player.user.username


def _overs_str(legal_balls):
    return f"{legal_balls // 6}.{legal_balls % 6}"


def innings_score(innings):
    """Totals for an innings: runs, wickets, legal balls, overs, extras."""
    rows = _deliveries(innings)
    legal = sum(1 for d in rows if d.is_legal)
    return {
        'runs': sum(d.total_runs for d in rows),
        'wickets': sum(1 for d in rows if d.is_wicket),
        'legal_balls': legal,
        'overs': _overs_str(legal),
        'extras': sum(d.extra_runs for d in rows),
        'balls': len(rows),
    }


def active_retired_ids(innings, rows=None):
    """Players currently retired hurt: retired with no later delivery showing
    them back at the crease. They remain eligible to resume batting."""
    if rows is None:
        rows = _deliveries(innings)
    retired = set()
    for r in innings.retirements.all():
        returned = any(
            d.sequence > r.at_sequence and r.player_id in (d.striker_id, d.non_striker_id)
            for d in rows
        )
        if not returned:
            retired.add(r.player_id)
    return retired


def batting_card(innings):
    """Per-batter rows in the order they first appeared. Each: player, runs,
    balls, fours, sixes, strike_rate, out (bool), how_out."""
    rows = _deliveries(innings)
    order = []
    stats = {}
    for d in rows:
        for p in (d.striker, d.non_striker):
            if p and p.id not in stats:
                order.append(p.id)
                stats[p.id] = {
                    'player': p, 'runs': 0, 'balls': 0, 'fours': 0,
                    'sixes': 0, 'out': False, 'how_out': '',
                }
        s = stats[d.striker_id]
        s['runs'] += d.runs_off_bat
        if d.extra_type != Delivery.EXTRA_WIDE:  # no-ball counts as faced; wide doesn't
            s['balls'] += 1
        if d.runs_off_bat == 4:
            s['fours'] += 1
        elif d.runs_off_bat == 6:
            s['sixes'] += 1
        if d.is_wicket and d.out_player_id in stats:
            o = stats[d.out_player_id]
            o['out'] = True
            o['how_out'] = _how_out(d)
    # Retired hurt is not a dismissal: out stays False, only the label changes.
    for pid in active_retired_ids(innings, rows):
        if pid in stats and not stats[pid]['out']:
            stats[pid]['how_out'] = 'retired hurt'
    cards = []
    for pid in order:
        s = stats[pid]
        s['strike_rate'] = round(s['runs'] * 100 / s['balls'], 1) if s['balls'] else 0.0
        cards.append(s)
    return cards


def _how_out(d):
    kind = d.dismissal_type or 'out'
    bowler = _name(d.bowler)
    fielder = _name(d.fielder)
    if kind == 'caught':
        return f"c {fielder} b {bowler}" if fielder else f"c & b {bowler}"
    if kind == 'runout':
        return f"run out ({fielder})" if fielder else "run out"
    if kind == 'stumped':
        return f"st {fielder} b {bowler}"
    if kind in ('bowled', 'lbw', 'hitwicket'):
        return f"{kind} {bowler}"
    return kind


def bowling_card(innings):
    """Per-bowler rows in first-appearance order: player, overs, balls (legal),
    runs (conceded), wickets, economy."""
    rows = _deliveries(innings)
    order = []
    stats = {}
    for d in rows:
        if d.bowler_id not in stats:
            order.append(d.bowler_id)
            stats[d.bowler_id] = {
                'player': d.bowler, 'balls': 0, 'runs': 0, 'wickets': 0,
            }
        b = stats[d.bowler_id]
        if d.is_legal:
            b['balls'] += 1
        b['runs'] += d.runs_conceded
        if d.is_wicket and d.dismissal_type in Delivery.BOWLER_DISMISSALS:
            b['wickets'] += 1
    cards = []
    for pid in order:
        b = stats[pid]
        b['overs'] = _overs_str(b['balls'])
        b['economy'] = round(b['runs'] * 6 / b['balls'], 2) if b['balls'] else 0.0
        cards.append(b)
    return cards


def fall_of_wickets(innings):
    """[{wicket, score, player, overs}] in order of dismissal."""
    rows = _deliveries(innings)
    running = 0
    legal = 0
    out = []
    for d in rows:
        running += d.total_runs
        if d.is_legal:
            legal += 1
        if d.is_wicket:
            out.append({
                'wicket': len(out) + 1,
                'score': running,
                'player': d.out_player,
                'overs': _overs_str(legal),
            })
    return out


def extras_breakdown(innings):
    """{wide, noball, bye, legbye, total} run counts for the innings."""
    out = {'wide': 0, 'noball': 0, 'bye': 0, 'legbye': 0}
    for d in _deliveries(innings):
        if d.extra_type in out:
            out[d.extra_type] += d.extra_runs
    out['total'] = out['wide'] + out['noball'] + out['bye'] + out['legbye']
    return out


# ── Awards: caps + player of the match / session ─────────────────────────────

# Impact weights for the auto-pick. Runs count 1-for-1; wickets and dismissals
# in the field are scaled so a match-winning bowling/fielding spell can out-rank
# a big batting score. Tunable in one place — every award reads these.
_WICKET_PTS = 20
_CATCH_PTS = 10
_STUMP_PTS = 10
_RUNOUT_PTS = 8


def _impact(a):
    """Single comparable number for an aggregate row — the auto Player-of-the-X."""
    return (a['runs']
            + a['wickets'] * _WICKET_PTS
            + a['catches'] * _CATCH_PTS
            + a['stumpings'] * _STUMP_PTS
            + a['runouts'] * _RUNOUT_PTS)


def _award_rows(deliveries, by='player'):
    """Per-contributor batting/bowling/fielding tallies across `deliveries`.

    `by='player'` keys on Player.id — right for a single match, where each user
    has exactly one Player row. `by='user'` keys on User.id so a user's lines
    across several matches in a session collapse into one row (their Player
    differs per match). Returns {key: {player, user, runs, balls, wickets,
    conceded, catches, runouts, stumpings}}.
    """
    rows = {}

    def slot(player):
        key = player.id if by == 'player' else player.user_id
        if key not in rows:
            rows[key] = {
                'player': player, 'user': player.user,
                'runs': 0, 'balls': 0, 'wickets': 0, 'conceded': 0,
                'catches': 0, 'runouts': 0, 'stumpings': 0,
            }
        return rows[key]

    for d in deliveries:
        s = slot(d.striker)
        s['runs'] += d.runs_off_bat
        if d.extra_type != Delivery.EXTRA_WIDE:  # wide isn't a ball faced
            s['balls'] += 1
        b = slot(d.bowler)
        b['conceded'] += d.runs_conceded
        if d.is_wicket and d.dismissal_type in Delivery.BOWLER_DISMISSALS:
            b['wickets'] += 1
        if d.is_wicket and d.fielder_id:
            f = slot(d.fielder)
            if d.dismissal_type == 'caught':
                f['catches'] += 1
            elif d.dismissal_type == 'runout':
                f['runouts'] += 1
            elif d.dismissal_type == 'stumped':
                f['stumpings'] += 1
    return rows


def _match_deliveries(match):
    return list(
        Delivery.objects.filter(innings__match=match).select_related(
            'striker__user', 'bowler__user', 'fielder__user',
        )
    )


def match_awards(match):
    """Orange cap (most runs), purple cap (most wickets) and Player of the Match
    for a single match, derived from its ledger.

    `mom_player` resolves the staff override first, falling back to the auto
    pick (highest impact); `mom_is_override` says which. All keys may be None
    before any ball is bowled. `mom_stats` is the aggregate row for the chosen
    player (None if an override player never took the field)."""
    agg = _award_rows(_match_deliveries(match), by='player')
    vals = list(agg.values())

    # Most runs — tie broken by fewer balls (the brisker knock).
    orange = max(
        (v for v in vals if v['runs'] > 0),
        key=lambda v: (v['runs'], -v['balls']), default=None,
    )
    # Most wickets — tie broken by fewer runs conceded.
    purple = max(
        (v for v in vals if v['wickets'] > 0),
        key=lambda v: (v['wickets'], -v['conceded']), default=None,
    )
    auto = max(vals, key=_impact, default=None)
    if auto is not None and _impact(auto) == 0:
        auto = None  # nobody scored, bowled a wicket, or held a catch yet

    override = match.man_of_match
    if override is not None:
        mom_player, mom_stats = override, agg.get(override.id)
    elif auto is not None:
        mom_player, mom_stats = auto['player'], auto
    else:
        mom_player, mom_stats = None, None

    return {
        'orange': orange,
        'purple': purple,
        'mom_player': mom_player,
        'mom_stats': mom_stats,
        'mom_auto_player': auto['player'] if auto else None,
        'mom_is_override': override is not None,
    }


def session_awards(session):
    """Player of the Session — highest combined impact across every match in the
    session. Aggregated by user (one user, many Player rows across matches).
    Returns None until at least one contribution exists."""
    rows = list(
        Delivery.objects.filter(innings__match__session=session).select_related(
            'striker__user', 'bowler__user', 'fielder__user',
        )
    )
    if not rows:
        return None
    agg = _award_rows(rows, by='user')
    best = max(agg.values(), key=_impact, default=None)
    if best is None or _impact(best) == 0:
        return None
    return {
        'user': best['user'],
        'runs': best['runs'],
        'wickets': best['wickets'],
        'fielding': best['catches'] + best['stumpings'] + best['runouts'],
        'impact': _impact(best),
    }


def career_stats(user):
    """Lifelong batting / bowling / fielding aggregates for a user, derived from
    every delivery they were involved in. Returns dicts ready for the profile."""
    # Batting — group the user's faced deliveries by innings (for HS, NO, 50s).
    bat = {}
    for d in Delivery.objects.filter(striker__user=user).select_related('innings'):
        e = bat.setdefault(d.innings_id, {'runs': 0, 'balls': 0, 'out': False,
                                          'fours': 0, 'sixes': 0, 'match': d.innings.match_id})
        e['runs'] += d.runs_off_bat
        if d.extra_type != Delivery.EXTRA_WIDE:
            e['balls'] += 1
        if d.runs_off_bat == 4:
            e['fours'] += 1
        elif d.runs_off_bat == 6:
            e['sixes'] += 1
    for d in Delivery.objects.filter(out_player__user=user, is_wicket=True):
        if d.innings_id in bat:
            bat[d.innings_id]['out'] = True

    b_inns = len(bat)
    runs = sum(e['runs'] for e in bat.values())
    balls = sum(e['balls'] for e in bat.values())
    outs = sum(1 for e in bat.values() if e['out'])
    hs = max((e['runs'] for e in bat.values()), default=0)
    hs_no = any(e['runs'] == hs and not e['out'] for e in bat.values())
    batting = {
        'innings': b_inns, 'runs': runs, 'balls': balls, 'not_outs': b_inns - outs,
        'hs': hs, 'hs_label': f"{hs}{'*' if hs_no else ''}",
        'avg': round(runs / outs, 2) if outs else None,
        'sr': round(runs * 100 / balls, 2) if balls else None,
        'fours': sum(e['fours'] for e in bat.values()),
        'sixes': sum(e['sixes'] for e in bat.values()),
        'fifties': sum(1 for e in bat.values() if 50 <= e['runs'] < 100),
        'hundreds': sum(1 for e in bat.values() if e['runs'] >= 100),
    }

    # Bowling — group by innings (for best figures).
    bowl = {}
    for d in Delivery.objects.filter(bowler__user=user).select_related('innings'):
        e = bowl.setdefault(d.innings_id, {'balls': 0, 'runs': 0, 'wkts': 0, 'match': d.innings.match_id})
        if d.is_legal:
            e['balls'] += 1
        e['runs'] += d.runs_conceded
        if d.is_wicket and d.dismissal_type in Delivery.BOWLER_DISMISSALS:
            e['wkts'] += 1
    bo_balls = sum(e['balls'] for e in bowl.values())
    bo_runs = sum(e['runs'] for e in bowl.values())
    wkts = sum(e['wkts'] for e in bowl.values())
    best = None
    if bowl:
        b = sorted(bowl.values(), key=lambda e: (-e['wkts'], e['runs']))[0]
        best = f"{b['wkts']}/{b['runs']}"
    bowling = {
        'innings': len(bowl), 'overs': f"{bo_balls // 6}.{bo_balls % 6}", 'balls': bo_balls,
        'runs': bo_runs, 'wickets': wkts, 'best': best,
        'avg': round(bo_runs / wkts, 2) if wkts else None,
        'econ': round(bo_runs * 6 / bo_balls, 2) if bo_balls else None,
    }

    fielding = {
        'catches': Delivery.objects.filter(fielder__user=user, dismissal_type='caught').count(),
        'runouts': Delivery.objects.filter(fielder__user=user, dismissal_type='runout').count(),
        'stumpings': Delivery.objects.filter(fielder__user=user, dismissal_type='stumped').count(),
    }

    matches = len({e['match'] for e in bat.values()} | {e['match'] for e in bowl.values()})
    has_data = bool(b_inns or bowl or fielding['catches'] or fielding['runouts'] or fielding['stumpings'])
    return {'batting': batting, 'bowling': bowling, 'fielding': fielding,
            'matches': matches, 'has_data': has_data}


def player_recent_matches(user, limit=6):
    """A user's most recent matches (newest by session date) with their own
    batting/bowling line, for the WhatsApp HISTORY reply. Each dict:
    match, session, date, runs, balls, wickets, result (str|None), won (bool|None)."""
    match_ids = list(
        Player.objects.filter(user=user)
        .values_list('team__match_id', flat=True).distinct()
    )
    if not match_ids:
        return []
    matches = (
        Match.objects.filter(id__in=match_ids)
        .select_related('session', 'winner')
        .order_by('-session__date', '-id')[:limit]
    )
    out = []
    for m in matches:
        bat = list(Delivery.objects.filter(innings__match=m, striker__user=user))
        runs = sum(d.runs_off_bat for d in bat)
        balls = sum(1 for d in bat if d.extra_type != Delivery.EXTRA_WIDE)
        wkts = Delivery.objects.filter(
            innings__match=m, bowler__user=user, is_wicket=True,
            dismissal_type__in=Delivery.BOWLER_DISMISSALS,
        ).count()
        team_ids = set(
            Player.objects.filter(user=user, team__match=m).values_list('team_id', flat=True)
        )
        won = (m.winner_id in team_ids) if m.winner_id else None
        out.append({
            'match': m, 'session': m.session,
            'date': m.session.date if m.session else None,
            'runs': runs, 'balls': balls, 'wickets': wkts,
            'result': result_line(m), 'won': won,
        })
    return out


def result_line(match):
    """Human result once both innings are closed, e.g. 'A won by 12 runs' or
    'B won by 3 wickets'. Returns None while the match is still in progress."""
    innings = list(match.innings.order_by('number'))
    if len(innings) < 2 or not all(i.is_closed for i in innings):
        return None
    first, second = innings[0], innings[1]
    r1 = innings_score(first)['runs']
    s2 = innings_score(second)
    if r1 > s2['runs']:
        margin = r1 - s2['runs']
        return f"{first.batting_team.name} won by {margin} run{'' if margin == 1 else 's'}"
    if s2['runs'] > r1:
        roster = second.batting_team.players.count()
        allowed = roster if second.single_batting else roster - 1
        left = max(0, allowed - s2['wickets'])
        return f"{second.batting_team.name} won by {left} wicket{'' if left == 1 else 's'}"
    return "Match tied"


def this_over(innings):
    """Deliveries belonging to the latest over (for the timeline strip)."""
    rows = _deliveries(innings)
    if not rows:
        return []
    current = max(d.over_number for d in rows)
    return [d for d in rows if d.over_number == current]


def on_strike_for_next(innings):
    """Best-effort suggestion of (striker, non_striker) for the next ball, or
    None if no balls bowled yet (caller supplies openers). After a wicket the
    vacated end is returned as None — the scorer picks the incoming batter.
    """
    rows = _deliveries(innings)
    if not rows:
        return None
    last = rows[-1]
    striker, non_striker = last.striker, last.non_striker

    # Lone batter (last man stands): no partner to cross with — they keep
    # the strike for every ball until out.
    if non_striker is None:
        if last.is_wicket and last.out_player_id == striker.id:
            striker = None
        return striker, None

    # Runs physically run by the batters cause them to cross (odd → swap).
    crossing = last.runs_off_bat
    if last.extra_type in (Delivery.EXTRA_BYE, Delivery.EXTRA_LEGBYE):
        crossing += last.extra_runs
    elif last.extra_type in (Delivery.EXTRA_WIDE, Delivery.EXTRA_NOBALL):
        crossing += max(0, last.extra_runs - 1)  # exclude the 1-run penalty
    if crossing % 2 == 1:
        striker, non_striker = non_striker, striker

    # End of over → strike swaps (new bowler from the other end).
    legal = sum(1 for d in rows if d.is_legal)
    if last.is_legal and legal % 6 == 0:
        striker, non_striker = non_striker, striker

    # Dismissed batter's end is vacant — scorer picks the incoming batter.
    if last.is_wicket:
        if striker is not None and last.out_player_id == striker.id:
            striker = None
        elif non_striker is not None and last.out_player_id == non_striker.id:
            non_striker = None
    return striker, non_striker


def target_for(innings):
    """Runs the (2nd-innings) batting team needs to WIN — first-innings total + 1.
    Returns None for the first innings or if there's no first innings yet."""
    if innings.number < 2:
        return None
    first = innings.match.innings.filter(number=1).first()
    if first is None:
        return None
    return innings_score(first)['runs'] + 1


def is_innings_complete(innings):
    """True if the innings has ended: all out, overs cap reached, target chased
    down (2nd innings), or manually closed."""
    if innings.is_closed:
        return True
    score = innings_score(innings)
    roster = innings.batting_team.players.count()
    # Normally the innings ends one wicket early (no partner left); with
    # last-man-stands it runs until every batter is out.
    allowed_wickets = roster if innings.single_batting else roster - 1
    if roster and score['wickets'] >= allowed_wickets:
        return True
    limit = innings.match.overs_limit
    if limit and score['legal_balls'] >= limit * 6:
        return True
    # Chase: the 2nd innings ends the instant the target is reached.
    target = target_for(innings)
    if target is not None and score['runs'] >= target:
        return True
    return False


# ── Writes (transactional) ───────────────────────────────────────────────────

def sync_team_cache(innings):
    """Keep the denormalized Team.runs / Team.wickets in step with the ledger so
    existing chips/history keep working without template changes."""
    score = innings_score(innings)
    team = innings.batting_team
    team.runs = score['runs']
    team.wickets = score['wickets']
    team.save(update_fields=['runs', 'wickets'])


@transaction.atomic
def record_delivery(innings, *, striker, bowler, non_striker=None,
                    runs_off_bat=0, extra_type=Delivery.EXTRA_NONE, extra_runs=0,
                    is_wicket=False, dismissal_type='', out_player=None,
                    fielder=None, client_uuid=''):
    """Append one ball to the innings ledger and re-sync the Team cache.

    Idempotent on client_uuid: a duplicate POST returns the existing row instead
    of creating another (online retry now; offline replay later).
    """
    if client_uuid:
        existing = innings.deliveries.filter(client_uuid=client_uuid).first()
        if existing:
            return existing

    rows = _deliveries(innings)
    legal_before = sum(1 for d in rows if d.is_legal)
    sequence = (rows[-1].sequence + 1) if rows else 1

    delivery = Delivery.objects.create(
        innings=innings,
        sequence=sequence,
        client_uuid=client_uuid,
        over_number=legal_before // 6,
        ball_in_over=legal_before % 6 + 1,
        striker=striker,
        non_striker=non_striker,
        bowler=bowler,
        runs_off_bat=runs_off_bat,
        extra_type=extra_type,
        extra_runs=extra_runs,
        is_wicket=is_wicket,
        dismissal_type=dismissal_type,
        out_player=out_player if is_wicket else None,
        fielder=fielder if is_wicket else None,
    )
    sync_team_cache(innings)
    return delivery


@transaction.atomic
def undo_last(innings):
    """Delete the most recent ball and re-sync the Team cache. Returns it (or None)."""
    last = innings.deliveries.order_by('-sequence').first()
    if last is not None:
        last.delete()
        sync_team_cache(innings)
    return last


def start_innings(match, *, number, batting_team, bowling_team, striker, non_striker, bowler):
    """Create an innings and set the opening working-state."""
    return Innings.objects.create(
        match=match, number=number,
        batting_team=batting_team, bowling_team=bowling_team,
        current_striker=striker, current_non_striker=non_striker, current_bowler=bowler,
    )


def advance_after_delivery(innings):
    """Recompute the live working-state (who's on strike / bowling next) from the
    ledger. Striker is left None after a wicket and bowler None at over end — the
    scorer then picks the incoming batter / new bowler."""
    rows = _deliveries(innings)
    if not rows:
        return
    last = rows[-1]
    pair = on_strike_for_next(innings)
    if pair is not None:
        striker, non_striker = pair
        # An undo must not silently restore a retired-hurt batter to the
        # crease — leave their end vacant so the scorer re-picks.
        retired = active_retired_ids(innings, rows)
        if striker is not None and striker.id in retired:
            striker = None
        if non_striker is not None and non_striker.id in retired:
            non_striker = None
        innings.current_striker, innings.current_non_striker = striker, non_striker
    legal = sum(1 for d in rows if d.is_legal)
    innings.current_bowler = None if (last.is_legal and legal % 6 == 0) else last.bowler
    innings.save(update_fields=['current_striker', 'current_non_striker', 'current_bowler'])


@transaction.atomic
def retire_batter(innings, player):
    """Record a retired-hurt for a batter at the crease and vacate that end.
    Returns the Retirement, or None if the player isn't currently batting."""
    if innings.current_striker_id == player.id:
        innings.current_striker = None
    elif innings.current_non_striker_id == player.id:
        innings.current_non_striker = None
    else:
        return None
    last = innings.deliveries.order_by('-sequence').first()
    retirement = Retirement.objects.create(
        innings=innings, player=player,
        at_sequence=last.sequence if last else 0,
    )
    innings.save(update_fields=['current_striker', 'current_non_striker'])
    return retirement


@transaction.atomic
def score_ball(innings, *, runs_off_bat=0, extra_type=Delivery.EXTRA_NONE, extra_runs=0,
               is_wicket=False, dismissal_type='', out_player=None, fielder=None, client_uuid=''):
    """Record one ball using the innings' current working-state, then advance it."""
    delivery = record_delivery(
        innings,
        striker=innings.current_striker,
        non_striker=innings.current_non_striker,
        bowler=innings.current_bowler,
        runs_off_bat=runs_off_bat, extra_type=extra_type, extra_runs=extra_runs,
        is_wicket=is_wicket, dismissal_type=dismissal_type,
        out_player=out_player or (innings.current_striker if is_wicket else None),
        fielder=fielder, client_uuid=client_uuid,
    )
    advance_after_delivery(innings)
    return delivery


@transaction.atomic
def finalize_match_result(match):
    """Set Match.winner by comparing innings totals once both are closed.
    Returns the winning Team, or None (tie / not ready)."""
    innings = list(match.innings.all())
    if len(innings) < 2 or not all(i.is_closed for i in innings):
        return None
    scored = [(i.batting_team, innings_score(i)['runs']) for i in innings]
    scored.sort(key=lambda t: t[1], reverse=True)
    winner = scored[0][0] if scored[0][1] > scored[1][1] else None
    match.winner = winner
    match.save(update_fields=['winner'])
    return winner
