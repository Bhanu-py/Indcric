import uuid

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Match, Team, Player, Innings
from . import scoring

from rest_framework.response import Response
from rest_framework.views import APIView
from .models import TemporaryScoringPeriod

class GrantTemporaryScoringAccess(APIView):
    def post(self, request):
        # Get the session ID from the request
        session_id = self.request.data['session_id']
        
        # Create a new temporary scoring period
        temp_scoring_period = TemporaryScoringPeriod.objects.create(
            start_time=self.request.data['start_time'],
            end_time=self.request.data['end_time']
        )
        
        # Assign players and teams to the temporary scoring period
        temp_scoring_period.players.set(self.request.data['players'])
        temp_scoring_period.teams.set(self.request.data['teams'])
        
        return Response({'message': 'Temporary scoring access granted'})

class RevokeTemporaryScoringAccess(APIView):
    def post(self, request):
        # Get the session ID from the request
        session_id = self.request.data['session_id']
        
        # Delete the temporary scoring period
        TemporaryScoringPeriod.objects.filter(session__id=session_id).delete()
        
        return Response({'message': 'Temporary scoring access revoked'})

@login_required
def scorecard_view(request, match_id):
    """Read-only scorecard for everyone — both innings, batting/bowling cards,
    fall of wickets, and the result."""
    match = get_object_or_404(Match, id=match_id)
    innings_list = list(match.innings.order_by('number'))

    cards = []
    for inn in innings_list:
        score = scoring.innings_score(inn)
        legal = score['legal_balls']
        cards.append({
            'innings': inn,
            'batting_team': inn.batting_team,
            'score': score,
            'rr': round(score['runs'] * 6 / legal, 2) if legal else 0.0,
            'batting': scoring.batting_card(inn),
            'bowling': scoring.bowling_card(inn),
            'fow': scoring.fall_of_wickets(inn),
            'extras': scoring.extras_breakdown(inn),
        })

    return render(request, 'cric/pages/scorecard.html', {
        'match': match,
        'cards': cards,
        'result_line': scoring.result_line(match),
        'in_progress': bool(innings_list) and not all(i.is_closed for i in innings_list),
    })


def match_detail_view(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    teams = match.teams.all()
    team1 = team2 = None
    team1_players = team2_players = []
    if teams.count() >= 2:
        team1 = teams[0]
        team2 = teams[1]
        team1_players = team1.players.select_related('user').all()
        team2_players = team2.players.select_related('user').all()
    context = {
        'match': match,
        'team1': team1,
        'team2': team2,
        'team1_players': team1_players,
        'team2_players': team2_players,
    }
    return render(request, 'cric/pages/match_detail.html', context)


# ── Live scoring ─────────────────────────────────────────────────────────────

def _ball_token(d):
    """Short label for a delivery in the current-over timeline."""
    if d.extra_type == d.EXTRA_WIDE:
        extra = d.extra_runs - 1
        return ('wide', f"wd{('+' + str(extra)) if extra else ''}")
    if d.extra_type == d.EXTRA_NOBALL:
        return ('noball', f"nb{('+' + str(d.runs_off_bat)) if d.runs_off_bat else ''}")
    if d.extra_type == d.EXTRA_BYE:
        return ('bye', f"{d.extra_runs}b")
    if d.extra_type == d.EXTRA_LEGBYE:
        return ('legbye', f"{d.extra_runs}lb")
    if d.is_wicket:
        return ('wicket', f"W{('+' + str(d.runs_off_bat)) if d.runs_off_bat else ''}")
    if d.runs_off_bat in (4, 6):
        return ('boundary', str(d.runs_off_bat))
    return ('runs', str(d.runs_off_bat))


def _console_context(innings):
    score = scoring.innings_score(innings)
    complete = scoring.is_innings_complete(innings)

    # Chase info for the 2nd innings: target, runs needed, balls remaining.
    chase = None
    target = scoring.target_for(innings)
    if target is not None:
        limit = innings.match.overs_limit
        needed = max(0, target - score['runs'])
        balls_left = (limit * 6 - score['legal_balls']) if limit else None
        chase = {
            'target': target,
            'needed': needed,
            'balls_left': balls_left,
            'rrr': round(needed * 6 / balls_left, 2) if balls_left else None,
        }

    out_ids = set(
        innings.deliveries.filter(is_wicket=True).values_list('out_player_id', flat=True)
    )
    crease_ids = {innings.current_striker_id, innings.current_non_striker_id}
    available_batters = [
        p for p in innings.batting_team.players.select_related('user').order_by('id')
        if p.id not in out_ids and p.id not in crease_ids
    ]
    last = innings.deliveries.order_by('-sequence').first()
    # The consecutive-overs rule only bites at an over boundary; mid-over (an
    # injury replacement or a mis-tapped "change bowler") anyone may take over.
    at_over_boundary = score['legal_balls'] % 6 == 0
    prev_bowler_id = last.bowler_id if (last and at_over_boundary) else None
    available_bowlers = [
        p for p in innings.bowling_team.players.select_related('user').order_by('id')
        if p.id != prev_bowler_id
    ]

    # Either end can be vacant: a wicket, a run-out of the non-striker, or a
    # retired hurt all leave a hole the scorer must fill before the next ball.
    # Under last-man-stands the empty non-striker end is the normal state.
    need_batter = (
        innings.current_striker_id is None
        or (innings.current_non_striker_id is None and not innings.single_batting)
    ) and not complete
    need_bowler = (not need_batter) and innings.current_bowler_id is None and not complete

    # Last-man-stands offer: the innings just ended on its final wicket (not
    # overs / target), a survivor is still at the crease, and the option
    # hasn't been taken yet.
    roster = innings.batting_team.players.count()
    overs_done = bool(innings.match.overs_limit) and score['legal_balls'] >= innings.match.overs_limit * 6
    chased = chase is not None and chase['needed'] == 0
    can_single_bat = (
        complete and not innings.is_closed and not innings.single_batting
        and not overs_done and not chased
        and roster and score['wickets'] == roster - 1
        and (innings.current_striker_id or innings.current_non_striker_id)
    )

    legal = score['legal_balls']
    over_balls = [
        {'kind': k, 'token': t}
        for k, t in (_ball_token(d) for d in scoring.this_over(innings))
    ]

    batting = scoring.batting_card(innings)
    bowling = scoring.bowling_card(innings)
    bat_by_id = {row['player'].id: row for row in batting}
    bowl_by_id = {row['player'].id: row for row in bowling}

    return {
        'innings': innings,
        'match': innings.match,
        'score': score,
        'overs_limit': innings.match.overs_limit,
        'chase': chase,
        'crr': round(score['runs'] * 6 / legal, 2) if legal else 0.0,
        'batting': batting,
        'bowling': bowling,
        'striker': innings.current_striker,
        'non_striker': innings.current_non_striker,
        'bowler': innings.current_bowler,
        'striker_stat': bat_by_id.get(innings.current_striker_id),
        'non_striker_stat': bat_by_id.get(innings.current_non_striker_id),
        'bowler_stat': bowl_by_id.get(innings.current_bowler_id),
        'over_balls': over_balls,
        'complete': complete,
        'need_batter': need_batter,
        'need_bowler': need_bowler,
        'can_single_bat': can_single_bat,
        'vacant_end': 'striker' if innings.current_striker_id is None else 'nonstriker',
        'retired_ids': scoring.active_retired_ids(innings),
        'ready': (not complete) and not need_batter and not need_bowler,
        'available_batters': available_batters,
        'available_bowlers': available_bowlers,
        'fielders': list(innings.bowling_team.players.select_related('user').order_by('id')),
        'is_first_innings': innings.number == 1,
        'min_overs': max(1, (score['legal_balls'] + 5) // 6),  # floor for mid-innings overs change
        'batting_players': list(innings.batting_team.players.select_related('user').order_by('id')),
        'ball_uuid': uuid.uuid4().hex,  # fresh per render → idempotent ball POST
        'extras_buttons': [('wide', 'Wd'), ('noball', 'NB'), ('bye', 'B'), ('legbye', 'LB')],
        'dismissals': [
            ('bowled', 'Bowled'), ('caught', 'Caught'), ('lbw', 'LBW'),
            ('runout', 'Run out'), ('stumped', 'Stumped'), ('hitwicket', 'Hit wkt'),
        ],
    }


def _render_console(request, innings):
    return render(request, 'cric/partials/_score_console.html', _console_context(innings))


def _staff_or_redirect(request, match):
    if request.user.is_staff:
        return None
    messages.error(request, "Only staff can score matches.")
    return redirect('session_detail', session_id=match.session_id)


@login_required
def score_view(request, match_id):
    """Scoring entry point. Shows the setup form for the next innings, or the
    live console for the innings in progress. Staff only."""
    match = get_object_or_404(Match, id=match_id)
    redirect_resp = _staff_or_redirect(request, match)
    if redirect_resp:
        return redirect_resp

    innings_list = list(match.innings.order_by('number'))
    active = next((i for i in innings_list if not i.is_closed), None)

    if active is not None:
        return render(request, 'cric/pages/score.html',
                      {'setup': False, **_console_context(active)})

    if len(innings_list) >= 2:
        # Both innings done — send to the session where the result now shows.
        scoring.finalize_match_result(match)
        result = scoring.result_line(match)
        messages.success(request, f"{match.name}: {result}" if result else f"{match.name} complete.")
        return redirect('session_detail', session_id=match.session_id)

    # Set up the next innings.
    teams = list(match.teams.order_by('id'))
    if len(teams) < 2:
        messages.error(request, "This match needs two teams before scoring.")
        return redirect('session_detail', session_id=match.session_id)

    number = len(innings_list) + 1
    forced_batting = None
    if number == 2:
        # Second innings: the side that bowled first now bats.
        forced_batting = innings_list[0].bowling_team

    teams_data = [{
        'id': t.id,
        'name': t.name,
        'players': [
            {'id': p.id, 'name': (p.user.first_name or p.user.username)}
            for p in t.players.select_related('user').order_by('id')
        ],
    } for t in teams]

    return render(request, 'cric/pages/score.html', {
        'setup': True,
        'match': match,
        'number': number,
        'teams': teams,
        'teams_data': teams_data,
        'forced_batting': forced_batting,
    })


@login_required
def start_innings_view(request, match_id):
    match = get_object_or_404(Match, id=match_id)
    redirect_resp = _staff_or_redirect(request, match)
    if redirect_resp:
        return redirect_resp
    if request.method != 'POST':
        return redirect('match_score', match_id=match.id)

    number = int(request.POST.get('number', 1))
    teams = {t.id: t for t in match.teams.all()}
    try:
        batting_team = teams[int(request.POST['batting_team'])]
        bowling_team = next(t for tid, t in teams.items() if tid != batting_team.id)
        striker = Player.objects.get(pk=request.POST['striker'], team=batting_team)
        non_striker = Player.objects.get(pk=request.POST['non_striker'], team=batting_team)
        bowler = Player.objects.get(pk=request.POST['bowler'], team=bowling_team)
    except (KeyError, ValueError, StopIteration, Player.DoesNotExist):
        messages.error(request, "Pick two batters and a bowler to start.")
        return redirect('match_score', match_id=match.id)

    if striker.id == non_striker.id:
        messages.error(request, "Striker and non-striker must be different players.")
        return redirect('match_score', match_id=match.id)

    if number == 1:
        try:
            match.overs_limit = max(1, int(request.POST.get('overs', 0)))
        except (ValueError, TypeError):
            messages.error(request, "Enter a valid overs limit.")
            return redirect('match_score', match_id=match.id)
        toss_winner_id = request.POST.get('toss_winner')
        if toss_winner_id and int(toss_winner_id) in teams:
            match.toss_winner = teams[int(toss_winner_id)]
        decision = request.POST.get('toss_decision', '')
        match.toss_decision = decision if decision in ('bat', 'bowl') else ''
        match.save(update_fields=['overs_limit', 'toss_winner', 'toss_decision'])

    scoring.start_innings(
        match, number=number, batting_team=batting_team, bowling_team=bowling_team,
        striker=striker, non_striker=non_striker, bowler=bowler,
    )
    return redirect('match_score', match_id=match.id)


def _active_innings_or_404(request, innings_id):
    return get_object_or_404(Innings, id=innings_id)


@login_required
def score_ball_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if not request.user.is_staff or request.method != 'POST':
        return _render_console(request, innings)
    if innings.is_closed or innings.current_striker_id is None or innings.current_bowler_id is None:
        return _render_console(request, innings)

    runs = max(0, min(7, int(request.POST.get('runs') or 0)))
    mode = request.POST.get('mode', 'runs')
    client_uuid = request.POST.get('uuid', '')

    kwargs = {'client_uuid': client_uuid}
    if request.POST.get('wicket'):
        dismissal = request.POST.get('dismissal', 'bowled')
        # Runs completed before the dismissal (run out going for the 2nd/3rd) —
        # the wicket panel posts its own field so the run buttons can't collide.
        wicket_runs = max(0, min(7, int(request.POST.get('wicket_runs') or 0)))
        kwargs.update(is_wicket=True, dismissal_type=dismissal, runs_off_bat=wicket_runs)
        fielder = None
        fielder_id = request.POST.get('fielder')
        if fielder_id:
            fielder = Player.objects.filter(pk=fielder_id, team=innings.bowling_team).first()
        # Fielding dismissals must name who did it — bounce invalid submits.
        if dismissal in ('caught', 'runout', 'stumped') and fielder is None:
            return _render_console(request, innings)
        kwargs['fielder'] = fielder
        # Run-out can dismiss either batter — honour the chosen end.
        if request.POST.get('out_end') == 'nonstriker' and innings.current_non_striker_id:
            kwargs['out_player'] = innings.current_non_striker
    elif mode == 'wide':
        kwargs.update(extra_type='wide', extra_runs=1 + runs)
    elif mode == 'noball':
        kwargs.update(extra_type='noball', extra_runs=1, runs_off_bat=runs)
    elif mode == 'bye':
        kwargs.update(extra_type='bye', extra_runs=runs)
    elif mode == 'legbye':
        kwargs.update(extra_type='legbye', extra_runs=runs)
    else:
        kwargs.update(runs_off_bat=runs)

    scoring.score_ball(innings, **kwargs)
    return _render_console(request, innings)


@login_required
def score_undo_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST':
        scoring.undo_last(innings)
        scoring.advance_after_delivery(innings)
    return _render_console(request, innings)


@login_required
def score_set_batter_view(request, innings_id):
    """Set the batter at either end. Default end=striker (the incoming-batter
    picker); end=nonstriker is used by the pre-first-ball opener fix. Picking
    the player already at the other end swaps them instead of duplicating."""
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST':
        player = Player.objects.filter(pk=request.POST.get('player'), team=innings.batting_team).first()
        if player:
            if request.POST.get('end') == 'nonstriker':
                if innings.current_striker_id == player.id:
                    innings.current_striker = innings.current_non_striker
                innings.current_non_striker = player
            else:
                if innings.current_non_striker_id == player.id:
                    innings.current_non_striker = innings.current_striker
                innings.current_striker = player
            innings.save(update_fields=['current_striker', 'current_non_striker'])
    return _render_console(request, innings)


@login_required
def score_single_batting_view(request, innings_id):
    """Last man stands: let the surviving batter continue alone after the
    would-be-final wicket. The lone batter always takes strike."""
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST' and not innings.is_closed:
        innings.single_batting = True
        if innings.current_striker_id is None:
            innings.current_striker = innings.current_non_striker
        innings.current_non_striker = None
        innings.save(update_fields=['single_batting', 'current_striker', 'current_non_striker'])
    return _render_console(request, innings)


@login_required
def score_retire_batter_view(request, innings_id):
    """Retired hurt: vacate the chosen batter's end without a wicket. The
    batter stays eligible to resume later from the next-batter picker."""
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST' and not innings.is_closed:
        player = Player.objects.filter(pk=request.POST.get('player'), team=innings.batting_team).first()
        if player:
            scoring.retire_batter(innings, player)
    return _render_console(request, innings)


@login_required
def score_swap_strike_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if (request.user.is_staff and request.method == 'POST' and not innings.is_closed
            and innings.current_striker_id and innings.current_non_striker_id):
        innings.current_striker, innings.current_non_striker = (
            innings.current_non_striker, innings.current_striker
        )
        innings.save(update_fields=['current_striker', 'current_non_striker'])
    return _render_console(request, innings)


@login_required
def score_change_bowler_view(request, innings_id):
    """Clear the current bowler so the console shows the bowler picker — covers
    a mid-over replacement and fixing a mistaken opening pick."""
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST' and not innings.is_closed:
        innings.current_bowler = None
        innings.save(update_fields=['current_bowler'])
    return _render_console(request, innings)


@login_required
def score_set_overs_view(request, innings_id):
    """Change the match overs cap mid-innings, floored at overs already begun."""
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST' and not innings.is_closed:
        try:
            new_limit = int(request.POST.get('overs', ''))
        except (TypeError, ValueError):
            new_limit = 0
        if new_limit:
            legal = scoring.innings_score(innings)['legal_balls']
            floor_overs = max(1, (legal + 5) // 6)
            match = innings.match
            match.overs_limit = max(floor_overs, min(50, new_limit))
            match.save(update_fields=['overs_limit'])
    return _render_console(request, innings)


@login_required
def score_set_bowler_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST':
        player = Player.objects.filter(pk=request.POST.get('player'), team=innings.bowling_team).first()
        if player:
            innings.current_bowler = player
            innings.save(update_fields=['current_bowler'])
    return _render_console(request, innings)


@login_required
def reopen_scoring_view(request, match_id):
    """Reopen the latest innings after it was closed, for last-ball mistakes
    noticed late. Only the most recent innings can reopen, so an earlier
    innings' total (the chase target) can never change retroactively. The
    result is cleared and recomputed when the innings is finished again."""
    match = get_object_or_404(Match, id=match_id)
    redirect_resp = _staff_or_redirect(request, match)
    if redirect_resp:
        return redirect_resp
    if request.method == 'POST':
        latest = match.innings.order_by('-number').first()
        if latest and latest.is_closed:
            latest.is_closed = False
            latest.save(update_fields=['is_closed'])
            if match.winner_id is not None:
                match.winner = None
                match.save(update_fields=['winner'])
        return redirect('match_score', match_id=match.id)
    return redirect('scorecard', match_id=match.id)


@login_required
def end_innings_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST':
        innings.is_closed = True
        innings.save(update_fields=['is_closed'])
        if innings.number >= 2:
            scoring.finalize_match_result(innings.match)
    return redirect('match_score', match_id=innings.match_id)
