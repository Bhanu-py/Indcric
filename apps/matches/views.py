import uuid

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .models import Match, Team, Player, Innings
from . import scoring


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
        return ('wicket', 'W')
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
        chase = {
            'target': target,
            'needed': max(0, target - score['runs']),
            'balls_left': (limit * 6 - score['legal_balls']) if limit else None,
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
    prev_bowler_id = last.bowler_id if last else None
    available_bowlers = [
        p for p in innings.bowling_team.players.select_related('user').order_by('id')
        if p.id != prev_bowler_id
    ]

    need_batter = innings.current_striker_id is None and not complete
    need_bowler = (not need_batter) and innings.current_bowler_id is None and not complete

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
        'ready': (not complete) and not need_batter and not need_bowler,
        'available_batters': available_batters,
        'available_bowlers': available_bowlers,
        'fielders': list(innings.bowling_team.players.select_related('user').order_by('id')),
        'is_first_innings': innings.number == 1,
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
        messages.success(request, f"{match.name} complete.")
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
            match.save(update_fields=['overs_limit'])
        except (ValueError, TypeError):
            messages.error(request, "Enter a valid overs limit.")
            return redirect('match_score', match_id=match.id)

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
        kwargs.update(
            is_wicket=True,
            dismissal_type=request.POST.get('dismissal', 'bowled'),
            runs_off_bat=runs,
        )
        fielder_id = request.POST.get('fielder')
        if fielder_id:
            kwargs['fielder'] = Player.objects.filter(pk=fielder_id).first()
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
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST':
        player = Player.objects.filter(pk=request.POST.get('player'), team=innings.batting_team).first()
        if player:
            innings.current_striker = player
            innings.save(update_fields=['current_striker'])
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
def end_innings_view(request, innings_id):
    innings = get_object_or_404(Innings, id=innings_id)
    if request.user.is_staff and request.method == 'POST':
        innings.is_closed = True
        innings.save(update_fields=['is_closed'])
        if innings.number >= 2:
            scoring.finalize_match_result(innings.match)
    return redirect('match_score', match_id=innings.match_id)
