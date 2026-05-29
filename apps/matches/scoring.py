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

from .models import Innings, Delivery


# ── Derivation (pure reads) ──────────────────────────────────────────────────

def _deliveries(innings):
    return list(innings.deliveries.all())  # ordering = ['sequence']


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
    cards = []
    for pid in order:
        s = stats[pid]
        s['strike_rate'] = round(s['runs'] * 100 / s['balls'], 1) if s['balls'] else 0.0
        cards.append(s)
    return cards


def _how_out(d):
    kind = d.dismissal_type or 'out'
    bowler = d.bowler.user.username if d.bowler_id else ''
    fielder = d.fielder.user.username if d.fielder_id else ''
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


def is_innings_complete(innings):
    """True if the innings has ended: all out, overs cap reached, or closed."""
    if innings.is_closed:
        return True
    score = innings_score(innings)
    roster = innings.batting_team.players.count()
    if roster and score['wickets'] >= roster - 1:
        return True
    limit = innings.match.overs_limit
    if limit and score['legal_balls'] >= limit * 6:
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
        innings.current_striker, innings.current_non_striker = pair
    legal = sum(1 for d in rows if d.is_legal)
    innings.current_bowler = None if (last.is_legal and legal % 6 == 0) else last.bowler
    innings.save(update_fields=['current_striker', 'current_non_striker', 'current_bowler'])


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
