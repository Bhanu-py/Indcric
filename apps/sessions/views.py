from datetime import timedelta

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.db import models, transaction
from django.db.models import Sum
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal

from .models import Session, SessionPlayer, Attendance
from apps.matches.models import Match, Team, Player, Delivery
from apps.polls.models import Poll, Vote
from apps.payments.models import Payment, Wallet

User = get_user_model()


def home(request):
    today = timezone.now().date()
    upcoming_sessions = Session.objects.filter(date__gte=today).order_by('date', 'time')
    previous_sessions = Session.objects.filter(date__lt=today).order_by('-date', '-time')[:10]

    session_vote_counts = {}
    for session in list(upcoming_sessions) + list(previous_sessions):
        if hasattr(session, 'poll'):
            yes_votes = session.poll.votes.filter(choice='yes').count()
            no_votes = session.poll.votes.filter(choice='no').count()
            total_votes = yes_votes + no_votes
            yes_percentage = (yes_votes / total_votes * 100) if total_votes > 0 else 0
            session_vote_counts[session.id] = {
                'yes_votes': yes_votes,
                'no_votes': no_votes,
                'total_votes': total_votes,
                'yes_percentage': yes_percentage,
            }

    next_session = upcoming_sessions.first()
    next_session_votes = (
        session_vote_counts.get(next_session.id) if next_session else None
    )

    outstanding_total = Decimal('0')
    wallet_balance = Decimal('0')
    next_session_user_vote = None
    if request.user.is_authenticated:
        outstanding_total = (
            Payment.objects.filter(user=request.user, status='pending')
            .aggregate(total=Sum('amount')).get('total') or Decimal('0')
        )
        wallet_balance = (
            Wallet.objects.filter(user=request.user)
            .aggregate(total=Sum('amount')).get('total') or Decimal('0')
        )
        if next_session and hasattr(next_session, 'poll'):
            vote = Vote.objects.filter(
                poll=next_session.poll, user=request.user
            ).first()
            next_session_user_vote = vote.choice if vote else None

    context = {
        'upcoming_sessions': upcoming_sessions,
        'previous_sessions': previous_sessions,
        'vote_counts': session_vote_counts,
        'next_session': next_session,
        'next_session_votes': next_session_votes,
        'next_session_user_vote': next_session_user_vote,
        'outstanding_total': outstanding_total,
        'wallet_balance': wallet_balance,
    }
    return render(request, 'home.html', context)


@login_required
def create_session_view(request):
    if request.method == 'POST':
        name = request.POST['name']
        date_str = request.POST.get('date')
        time_str = request.POST.get('time')
        duration = request.POST.get('duration', 3)
        location = request.POST.get('location', '')
        cost = request.POST.get('cost', 0)

        try:
            duration = int(duration)
        except (ValueError, TypeError):
            duration = 3

        try:
            cost = float(cost)
        except (ValueError, TypeError):
            cost = 0.0

        date = time = None

        if not date_str:
            messages.error(request, "Date is required.")
            return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        if not time_str:
            messages.error(request, "Time is required.")
            return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        try:
            date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
            return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        try:
            time = timezone.datetime.strptime(time_str, '%H:%M').time()
        except ValueError:
            messages.error(request, "Invalid time format. Please use HH:MM.")
            return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        session = Session.objects.create(
            name=name, date=date, time=time, duration=duration,
            location=location, cost=cost, created_by=request.user,
        )
        poll = Poll.objects.create(
            session=session,
            question="Will you attend this session?",
            is_open=True,
        )

        messages.success(
            request,
            'Session created. Open the session page and tap '
            '"Share to WhatsApp Group" to invite members.'
        )
        return redirect('home')

    return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})


@login_required
def resend_poll_notifications_view(request, session_id):
    """Staff-only: nudge non-voters with a fresh session_rsvp DM.

    Defaults to scope='non_voters' (skip users who already voted) and enforces
    a 6-hour cooldown per recipient so double-clicks don't spam.

    Pass ?scope=all to override and re-fire to every phone-having member —
    useful when the initial broadcast failed entirely (template not approved,
    Meta outage, access-token issue).
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('session_detail', session_id=session_id)

    session = get_object_or_404(Session, id=session_id)
    if not hasattr(session, 'poll'):
        messages.error(request, "This session has no poll to send.")
        return redirect('session_detail', session_id=session_id)

    if request.method != 'POST':
        return redirect('session_detail', session_id=session_id)

    from apps.notifications.services import (
        resend_poll_invite, SCOPE_NON_VOTERS, SCOPE_ALL,
    )
    requested_scope = (request.POST.get('scope') or request.GET.get('scope') or '').strip().lower()
    scope = SCOPE_ALL if requested_scope == 'all' else SCOPE_NON_VOTERS

    try:
        result = resend_poll_invite(session.poll, scope=scope)
    except Exception:
        import logging
        logging.getLogger(__name__).exception(
            "Resend poll DMs failed for session %s", session.id
        )
        messages.error(request, 'Resend failed. Check Render logs.')
        return redirect('session_detail', session_id=session.id)

    sent = result['sent']
    skipped = result['skipped_cooldown']
    no_creds = result.get('skipped_no_creds', 0)
    failed = result['failed']
    targets = result['targets']

    if no_creds:
        messages.warning(
            request,
            'WhatsApp credentials not configured on this server — '
            f'{no_creds} DM(s) were not sent. Set WHATSAPP_PHONE_NUMBER_ID and '
            'WHATSAPP_ACCESS_TOKEN in the environment.'
        )
    elif sent:
        bits = [f"WhatsApp DM sent to {sent} member(s)"]
        if skipped:
            bits.append(f"{skipped} skipped (sent in last 6 h)")
        if failed:
            bits.append(f"{failed} failed — check logs")
        messages.success(request, '. '.join(bits) + '.')
    elif skipped and not failed:
        messages.info(
            request,
            f'No DMs sent — all {skipped} eligible recipient(s) were messaged in the last 6 hours.'
        )
    elif targets == 0:
        if scope == SCOPE_NON_VOTERS:
            messages.info(request, 'No DMs to send — everyone with a phone has already voted.')
        else:
            messages.warning(request, 'No DMs sent — no members have a phone on file.')
    else:
        messages.error(
            request,
            f'Resend failed for all {failed} target(s). Check Render logs for Meta error codes.'
        )

    return redirect('session_detail', session_id=session.id)


@login_required
def delete_session_view(request, session_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')

    session = get_object_or_404(Session, id=session_id)
    if request.method == 'POST':
        session_name = session.name
        session.delete()
        messages.success(request, f"Session '{session_name}' has been deleted.")
        return redirect('home')
    return redirect('session_detail', session_id=session_id)


@login_required
def session_detail_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)
    is_past = session.date < timezone.now().date()

    def _combined_rating(u):
        """Avg of batting/bowling/fielding ratings, rounded to 2dp. Defaults each None to 2.5."""
        bat  = u.batting_rating  if u.batting_rating  is not None else Decimal('2.5')
        bowl = u.bowling_rating  if u.bowling_rating  is not None else Decimal('2.5')
        fld  = u.fielding_rating if u.fielding_rating is not None else Decimal('2.5')
        return float(((bat + bowl + fld) / Decimal('3')).quantize(Decimal('0.01')))

    def _player_skills(u):
        """Per-skill numbers + combined rating for the team-balancer meter."""
        bat  = float(u.batting_rating  if u.batting_rating  is not None else Decimal('2.5'))
        bowl = float(u.bowling_rating  if u.bowling_rating  is not None else Decimal('2.5'))
        return {
            'batting': bat,
            'bowling': bowl,
            'rating': _combined_rating(u),
        }

    _ROLE_ORDER = {'batsman': 0, 'allrounder': 1, 'all-rounder': 1, 'bowler': 2}
    def _role_sort_key(p):
        return _ROLE_ORDER.get((p['user'].role or '').lower(), 3)

    user_vote = None
    yes_votes = no_votes = total_votes = 0
    yes_percentage = 0
    yes_voters = []
    no_voters = []
    if hasattr(session, 'poll'):
        poll = session.poll
        vote = Vote.objects.filter(poll=poll, user=request.user).first()
        user_vote = vote.choice if vote else None
        yes_votes = poll.votes.filter(choice='yes').count()
        no_votes = poll.votes.filter(choice='no').count()
        total_votes = yes_votes + no_votes
        if total_votes > 0:
            yes_percentage = (yes_votes / total_votes) * 100
        yes_voters = [{'user': v.user, 'team_assigned': False, **_player_skills(v.user)}
                      for v in poll.votes.filter(choice='yes').select_related('user')]
        no_voters = [v.user for v in poll.votes.filter(choice='no').select_related('user')]

    matches = list(session.matches.prefetch_related('teams__players__user').order_by('id'))

    edit_match_id = request.GET.get('edit_match')
    edit_match = edit_team1 = edit_team2 = None
    edit_team1_players = []
    edit_team2_players = []

    if edit_match_id:
        edit_match = get_object_or_404(Match, id=edit_match_id, session=session)
        teams = list(edit_match.teams.order_by('id'))
        if len(teams) >= 1:
            edit_team1 = teams[0]
            edit_team1_players = sorted([
                {'user': p.user, **_player_skills(p.user)}
                for p in edit_team1.players.select_related('user').all()
            ], key=_role_sort_key)
        if len(teams) >= 2:
            edit_team2 = teams[1]
            edit_team2_players = sorted([
                {'user': p.user, **_player_skills(p.user)}
                for p in edit_team2.players.select_related('user').all()
            ], key=_role_sort_key)

    assigned_ids = {p['user'].id for p in edit_team1_players + edit_team2_players}
    for voter in yes_voters:
        voter['team_assigned'] = voter['user'].id in assigned_ids

    # Staff can add any active member to the draft pool (e.g. late arrivals who
    # never voted) — everyone not already shown in the editor (pool + teams).
    addable_pool = []
    if request.user.is_staff:
        editor_ids = {v['user'].id for v in yes_voters} | assigned_ids
        for u in User.objects.filter(is_active=True).exclude(id__in=editor_ids).order_by('first_name', 'username'):
            addable_pool.append({
                'id': u.id, 'username': u.username, 'role': u.role or '',
                **_player_skills(u),
            })

    cost_per_person_est = None
    if not session.cost_per_person and yes_votes > 0 and session.cost:
        cost_per_person_est = (session.cost / Decimal(yes_votes)).quantize(Decimal('0.01'))

    # ── Attendance roster (only used by the embedded attendance card on past sessions) ──
    attendance_roster = []
    attendance_present_ids = []
    addable_users = []
    if is_past and hasattr(session, 'poll'):
        # Auto-create SessionPlayer rows for yes-voters so the roster is populated.
        # Default each new attendee to attended=True — the optimistic assumption is that
        # whoever voted Yes showed up. Staff unchecks no-shows and saves.
        yes_user_ids = list(session.poll.votes.filter(choice='yes').values_list('user_id', flat=True))
        for uid in yes_user_ids:
            sp, _ = SessionPlayer.objects.get_or_create(session=session, user_id=uid)
            Attendance.objects.get_or_create(match_player=sp, defaults={'attended': True})
        attendance_roster = list(
            SessionPlayer.objects.filter(session=session)
            .select_related('user')
            .order_by('user__username')
        )
        attendance_present_ids = list(
            Attendance.objects.filter(match_player__session=session, attended=True)
            .values_list('match_player_id', flat=True)
        )
        if request.user.is_staff:
            in_roster_ids = {sp.user_id for sp in attendance_roster}
            addable_users = list(
                User.objects.filter(is_active=True)
                .exclude(id__in=in_roster_ids)
                .order_by('username')
            )

    whatsapp_share_url = ''
    if hasattr(session, 'poll'):
        from apps.notifications.services import build_group_share_url
        base = request.build_absolute_uri('/')
        whatsapp_share_url = build_group_share_url(session.poll, base)

    context = {
        'session': session,
        'is_past': is_past,
        'attendance_roster': attendance_roster,
        'attendance_present_ids': attendance_present_ids,
        'user_vote': user_vote,
        'yes_votes': yes_votes,
        'no_votes': no_votes,
        'total_votes': total_votes,
        'yes_percentage': yes_percentage,
        'yes_voters': yes_voters,
        'no_voters': no_voters,
        'cost_per_person_est': cost_per_person_est,
        'addable_pool': addable_pool,
        'matches': matches,
        'edit_match': edit_match,
        'edit_team1': edit_team1,
        'edit_team2': edit_team2,
        'edit_team1_players': edit_team1_players,
        'edit_team2_players': edit_team2_players,
        'whatsapp_share_url': whatsapp_share_url,
        'addable_users': addable_users,
    }
    return render(request, 'cric/pages/session_detail.html', context)


@login_required
def vote_session_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    session = poll.session

    if request.method == 'POST':
        if not poll.is_open:
            messages.error(request, "This poll is closed.")
            return redirect('session_detail', session_id=session.id)
        if session.date < timezone.now().date():
            messages.error(request, "This session has already ended.")
            return redirect('session_detail', session_id=session.id)

        choice = request.POST.get('choice')
        if choice in ['yes', 'no']:
            Vote.objects.update_or_create(
                poll=poll, user=request.user, defaults={'choice': choice}
            )
            messages.success(request, f"Vote updated to '{choice}'.")
        elif choice == 'withdraw':
            Vote.objects.filter(poll=poll, user=request.user).delete()
            messages.success(request, "Your vote has been removed.")
        else:
            messages.error(request, "Invalid choice.")

    return redirect('session_detail', session_id=session.id)


@login_required
def close_poll_view(request, poll_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')

    poll = get_object_or_404(Poll, id=poll_id)
    session = poll.session

    if request.method == 'POST':
        poll.is_open = not poll.is_open
        poll.save()
        status = "opened" if poll.is_open else "closed"
        messages.success(request, f"Poll has been {status}.")

    return redirect('session_detail', session_id=session.id)


def _int_ids(str_ids):
    out = []
    for pid in str_ids:
        try:
            out.append(int(pid))
        except (ValueError, TypeError):
            pass
    return out


@transaction.atomic
def _sync_teams_in_place(match, teams, t1_name, t2_name, t1_ids, t2_ids, t1_cap_id, t2_cap_id):
    """Reconcile an already-scored match's teams to the posted line-ups without
    wiping anyone who has deliveries. Lets late players join mid-match (added to
    the unassigned pool → dragged onto a team) while protecting the ledger:
    players who've batted/bowled stay put and are never deleted or moved."""
    team1, team2 = teams[0], teams[1]
    team1.name = t1_name or team1.name
    team2.name = t2_name or team2.name
    if t1_cap_id:
        team1.captain = User.objects.filter(id=t1_cap_id).first()
    if t2_cap_id:
        team2.captain = User.objects.filter(id=t2_cap_id).first()
    team1.save(update_fields=['name', 'captain'])
    team2.save(update_fields=['name', 'captain'])

    want = {team1.id: set(_int_ids(t1_ids)), team2.id: set(_int_ids(t2_ids))}

    # Players already involved in scoring — locked in place.
    dq = Delivery.objects.filter(innings__match=match)
    involved_player_ids = set()
    for field in ('striker_id', 'non_striker_id', 'bowler_id', 'out_player_id', 'fielder_id'):
        involved_player_ids.update(
            dq.exclude(**{field + '__isnull': True}).values_list(field, flat=True)
        )
    involved_user_ids = set(
        Player.objects.filter(id__in=involved_player_ids).values_list('user_id', flat=True)
    )

    # Drop only players with no deliveries who are no longer on their team's list.
    for p in Player.objects.filter(team__in=(team1, team2)):
        if p.id in involved_player_ids:
            continue
        if p.user_id not in want[p.team_id]:
            p.delete()

    # Add newly listed players (skip anyone already scored on the other team).
    on_team = {}
    for p in Player.objects.filter(team__in=(team1, team2)):
        on_team.setdefault(p.team_id, set()).add(p.user_id)
    for team in (team1, team2):
        for uid in want[team.id]:
            if uid in on_team.get(team.id, set()) or uid in involved_user_ids:
                continue
            u = User.objects.filter(id=uid).first()
            if u:
                Player.objects.get_or_create(user=u, team=team, defaults={'role': u.role or 'batsman'})


@login_required
def save_teams_view(request, session_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('session_detail', session_id=session_id)

    session = get_object_or_404(Session, id=session_id)

    if request.method == 'POST':
        team1_name = request.POST.get('team1_name', 'Team 1')
        team2_name = request.POST.get('team2_name', 'Team 2')
        team1_players_str = request.POST.get('team1_players', '')
        team2_players_str = request.POST.get('team2_players', '')
        team1_captain_id = request.POST.get('team1_captain')
        team2_captain_id = request.POST.get('team2_captain')
        match_id = request.POST.get('match_id')
        match_name = request.POST.get('match_name', '').strip()

        team1_ids = [p for p in team1_players_str.split(',') if p.strip()]
        team2_ids = [p for p in team2_players_str.split(',') if p.strip()]
        if len(team1_ids) < 5 or len(team2_ids) < 5:
            messages.error(request, "Each team must have at least 5 players before saving.")
            return redirect('session_detail', session_id=session_id)

        if match_id:
            match = get_object_or_404(Match, id=match_id, session=session)
            if match_name:
                match.name = match_name
                match.save(update_fields=['name'])
        else:
            if session.date < timezone.now().date():
                messages.error(request, "This session has already ended — new matches can't be added.")
                return redirect('session_detail', session_id=session_id)
            match_number = session.matches.count() + 1
            match = Match.objects.create(
                session=session,
                name=match_name or f"Match {match_number}",
            )

        existing_teams = list(match.teams.order_by('id'))
        if existing_teams and Delivery.objects.filter(innings__match=match).exists():
            # Scoring has started — sync safely so late joiners can be added and
            # only unused players removed; never wipe someone who's already scored.
            _sync_teams_in_place(
                match, existing_teams,
                team1_name, team2_name, team1_ids, team2_ids,
                team1_captain_id, team2_captain_id,
            )
        else:
            match.teams.all().delete()
            team1_captain = User.objects.filter(id=team1_captain_id).first() if team1_captain_id else None
            team1 = Team.objects.create(match=match, name=team1_name, captain=team1_captain)
            for pid in team1_ids:
                try:
                    u = User.objects.get(id=int(pid))
                    Player.objects.create(user=u, team=team1, role=u.role)
                except (User.DoesNotExist, ValueError):
                    pass

            team2_captain = User.objects.filter(id=team2_captain_id).first() if team2_captain_id else None
            team2 = Team.objects.create(match=match, name=team2_name, captain=team2_captain)
            for pid in team2_ids:
                try:
                    u = User.objects.get(id=int(pid))
                    Player.objects.create(user=u, team=team2, role=u.role)
                except (User.DoesNotExist, ValueError):
                    pass

        messages.success(request, f"Teams saved for {match.name}!")

    return redirect('session_detail', session_id=session_id)


@login_required
def add_match_view(request, session_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('session_detail', session_id=session_id)

    session = get_object_or_404(Session, id=session_id)

    if session.date < timezone.now().date():
        messages.error(request, "This session has already ended — new matches can't be added.")
        return redirect('session_detail', session_id=session_id)

    if request.method == 'POST':
        last_match = session.matches.order_by('-id').first()
        match_number = session.matches.count() + 1
        new_match = Match.objects.create(session=session, name=f"Match {match_number}")
        if last_match:
            for old_team in last_match.teams.order_by('id'):
                new_team = Team.objects.create(
                    match=new_match, name=old_team.name, captain=old_team.captain
                )
                for old_player in old_team.players.select_related('user').all():
                    Player.objects.create(user=old_player.user, team=new_team, role=old_player.role)
        return redirect(f"{reverse('session_detail', args=[session_id])}?edit_match={new_match.id}")

    return redirect('session_detail', session_id=session_id)


@login_required
def record_score_view(request, match_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')

    match = get_object_or_404(Match, id=match_id)

    if request.method == 'POST':
        teams = list(match.teams.order_by('id'))
        if len(teams) >= 2:
            try:
                teams[0].runs = max(0, int(request.POST.get('team1_runs', 0)))
                teams[0].wickets = min(10, max(0, int(request.POST.get('team1_wickets', 0))))
                teams[0].save()
                teams[1].runs = max(0, int(request.POST.get('team2_runs', 0)))
                teams[1].wickets = min(10, max(0, int(request.POST.get('team2_wickets', 0))))
                teams[1].save()
                if teams[0].runs > teams[1].runs:
                    match.winner = teams[0]
                elif teams[1].runs > teams[0].runs:
                    match.winner = teams[1]
                else:
                    match.winner = None
                match.save()
                messages.success(request, f"Score saved for {match.name}.")
            except (ValueError, TypeError):
                messages.error(request, "Invalid score values.")

    return redirect('session_detail', session_id=match.session.id)


@login_required
def delete_match_view(request, match_id):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('home')

    match = get_object_or_404(Match, id=match_id)
    session_id = match.session.id

    if request.method == 'POST':
        with transaction.atomic():
            # Delete innings first — that cascade-removes their deliveries, which
            # otherwise PROTECT the players and block the match delete.
            match.innings.all().delete()
            match.delete()
        messages.success(request, f"{match.name} deleted.")

    return redirect('session_detail', session_id=session_id)


@login_required
def add_attendee_view(request, session_id):
    """Staff: add a player to the attendance roster after the session is past.

    For walk-ins who didn't vote on the poll. Creates a SessionPlayer and an
    Attendance row marked present, mirroring the auto-populate flow for
    yes-voters. The staff still has to hit Save attendance afterwards to
    recompute cost_per_person and sync Payment rows.
    """
    session = get_object_or_404(Session, pk=session_id)

    if request.method != 'POST':
        return redirect('session_detail', session_id=session.id)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('session_detail', session_id=session.id)

    user_id = request.POST.get('user_id')
    if not user_id:
        messages.error(request, "No player selected.")
        return redirect('session_detail', session_id=session.id)

    try:
        added_user = User.objects.get(pk=user_id, is_active=True)
    except (User.DoesNotExist, ValueError):
        messages.error(request, "That player wasn't found.")
        return redirect('session_detail', session_id=session.id)

    with transaction.atomic():
        sp, created = SessionPlayer.objects.get_or_create(session=session, user=added_user)
        Attendance.objects.get_or_create(match_player=sp, defaults={'attended': True})

    if created:
        messages.success(
            request,
            f"{added_user.get_full_name() or added_user.username} added to the roster. "
            "Hit Save attendance to apply the new cost split."
        )
    else:
        messages.info(request, f"{added_user.username} was already on the roster.")

    return redirect('session_detail', session_id=session.id)


@login_required
def session_attendance_detail_view(request, session_id):
    """POST target for the attendance form embedded in session_detail.html.

    Single save flow: every POST recomputes cost_per_person from the new
    attendee count and re-syncs Payment rows. Re-saving after toggling
    someone re-revises the split. Bare GETs redirect back to session detail
    (there's no standalone attendance page).
    """
    session = get_object_or_404(Session, pk=session_id)

    if request.method != 'POST':
        return redirect('session_detail', session_id=session.id)

    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('session_detail', session_id=session.id)

    present_sp_ids = set(request.POST.getlist('present'))

    with transaction.atomic():
        # 1. Sync each SessionPlayer's Attendance.attended.
        attendee_user_ids = []
        for sp in SessionPlayer.objects.filter(session=session).select_related('user'):
            is_present = str(sp.id) in present_sp_ids
            attendance, _ = Attendance.objects.get_or_create(
                match_player=sp, defaults={'attended': is_present}
            )
            if attendance.attended != is_present:
                attendance.attended = is_present
                attendance.save(update_fields=['attended'])
            if is_present:
                attendee_user_ids.append(sp.user_id)

        present_count = len(attendee_user_ids)

        # Genuinely nobody present → clear attendance entirely.
        if present_count == 0:
            session.cost_per_person = None
            session.attendance_confirmed = False
            session.save(update_fields=['cost_per_person', 'attendance_confirmed'])
            # Remove any pending payments — no one attended.
            Payment.objects.filter(session=session, status='pending').delete()
            messages.warning(request, 'No attendees marked — attendance cleared, no cost split.')
            return redirect('session_detail', session_id=session.id)

        # Attendees present but the session has no cost (free game) → still confirm
        # attendance, there's just nothing to split or collect.
        if not session.cost:
            session.cost_per_person = None
            session.attendance_confirmed = True
            session.save(update_fields=['cost_per_person', 'attendance_confirmed'])
            # No cost → drop stale pending payments; keep any historic paid records.
            Payment.objects.filter(session=session, status='pending').delete()
            messages.success(
                request,
                f'Attendance saved: {present_count} present. '
                'No cost set for this session, so there is nothing to split.'
            )
            return redirect('session_detail', session_id=session.id)

        # 2. Recompute the per-person split.
        cost_per_person = (session.cost / Decimal(present_count)).quantize(Decimal('0.01'))
        session.cost_per_person = cost_per_person
        session.attendance_confirmed = True
        session.save(update_fields=['cost_per_person', 'attendance_confirmed'])

        # 3. Sync Payment rows:
        #    - drop pending payments for users no longer attending
        #    - leave paid payments alone (historic record)
        #    - create/upsert pending payments for current attendees with the new amount
        attendee_set = set(attendee_user_ids)
        pending_removed = Payment.objects.filter(
            session=session, status='pending'
        ).exclude(user_id__in=attendee_set).delete()[0]

        # Warn about attendees being unchecked while a paid Payment exists.
        paid_unchecked = Payment.objects.filter(
            session=session, status='paid'
        ).exclude(user_id__in=attendee_set).select_related('user')
        for p in paid_unchecked:
            messages.warning(
                request,
                f"{p.user.username} has already paid €{p.amount} for this session "
                f"but is now unchecked. The paid record was kept; refund manually if needed."
            )

        for uid in attendee_set:
            payment, created = Payment.objects.get_or_create(
                user_id=uid, session=session,
                defaults={'amount': cost_per_person, 'status': 'pending', 'method': 'cash'},
            )
            if not created and payment.status == 'pending' and payment.amount != cost_per_person:
                payment.amount = cost_per_person
                payment.save(update_fields=['amount'])

    suffix = f' Removed {pending_removed} pending payment(s).' if pending_removed else ''
    messages.success(
        request,
        f'Attendance saved: {present_count} present, €{cost_per_person} per player.{suffix}'
    )
    return redirect('session_detail', session_id=session.id)


@login_required
def payments_view(request):
    """Cross-session payment tracking page.

    Two tabs (via ?tab=session|balances):
      - By session: pick a session, see attendees, toggle paid status
      - Member balances: list of members with outstanding totals, sorted desc

    POST handles per-payment toggle (paid ↔ pending) for the selected session.
    """
    today = timezone.now().date()
    thirty_days_ago = today - timedelta(days=30)

    # Snapshot strip ─────────────────────────────────────────────
    outstanding_total = (
        Payment.objects.filter(status='pending')
        .aggregate(total=Sum('amount')).get('total') or Decimal('0')
    )
    sessions_30d = Session.objects.filter(
        date__gte=thirty_days_ago, date__lte=today, attendance_confirmed=True
    ).count()
    # "Settled" = members with no pending payments (out of those who have any payments)
    members_with_payments = User.objects.filter(payment__isnull=False).distinct()
    settled_count = members_with_payments.exclude(
        payment__status='pending'
    ).distinct().count()
    members_with_payments_count = members_with_payments.count()

    # Paid sessions with confirmed attendance (the only ones that have Payment
    # rows). Free sessions (cost <= 0) never enter the payment flow — see below.
    confirmed_sessions = (
        Session.objects.filter(attendance_confirmed=True, cost__gt=0)
        .order_by('-date', '-time')
    )

    # Per-session payment rollup — drives the status chip on each card and lets
    # us sink fully-paid sessions to the bottom of the picker.
    session_pay = {
        row['session_id']: row
        for row in Payment.objects.values('session_id').annotate(
            total=models.Count('id'),
            paid=models.Count('id', filter=models.Q(status='paid')),
            outstanding=Sum('amount', filter=models.Q(status='pending')),
        )
    }

    def _build_card(s):
        agg = session_pay.get(s.id)
        total = agg['total'] if agg else 0
        paid = agg['paid'] if agg else 0
        return {
            'session': s,
            'total': total,
            'paid': paid,
            'fully_paid': total > 0 and paid == total,
            'outstanding': (agg['outstanding'] or Decimal('0')) if agg else Decimal('0'),
        }

    confirmed_cards = [_build_card(s) for s in confirmed_sessions]
    # Needs-payment cards stay up top; fully-settled ones drop to the archive strip.
    unsettled_cards = [c for c in confirmed_cards if not c['fully_paid']]
    settled_cards = [c for c in confirmed_cards if c['fully_paid']]

    # Paid past sessions whose attendance was never confirmed — not yet ready for
    # payments. Surfaced with a nudge to go confirm attendance first.
    pending_attendance_sessions = list(
        Session.objects.filter(date__lt=today, attendance_confirmed=False, cost__gt=0)
        .order_by('-date', '-time')
    )

    # Free past sessions (no cost) — nothing to split or collect, so they need no
    # attendance-confirm or payment workflow. Shown as 'Free', no action required.
    free_sessions = list(
        Session.objects.filter(date__lt=today, cost__lte=0)
        .order_by('-date', '-time')
    )

    # POST: toggle paid status for a selected session ────────────
    if request.method == 'POST':
        if not request.user.is_staff:
            messages.error(request, "You don't have permission to perform this action.")
            return redirect('manage-payments')
        session_id = request.POST.get('session_id')
        try:
            target_session = Session.objects.get(pk=session_id)
        except Session.DoesNotExist:
            messages.error(request, "Session not found.")
            return redirect('manage-payments')

        paid_user_ids = set(request.POST.getlist('paid_user'))
        deducted = []
        refunded = []
        with transaction.atomic():
            for payment in (
                Payment.objects.filter(session=target_session)
                .select_related('user')
            ):
                should_be_paid = str(payment.user_id) in paid_user_ids
                was_paid = payment.status == 'paid'
                was_wallet = payment.method == 'wallet'

                if should_be_paid and not was_paid:
                    # New confirmation. Decide method by current wallet balance:
                    # enough credit → debit wallet, otherwise record as cash/transfer.
                    balance = Wallet.objects.filter(user=payment.user).aggregate(
                        s=Sum('amount')
                    )['s'] or Decimal('0')
                    if balance >= payment.amount:
                        Wallet.objects.create(
                            user=payment.user,
                            amount=-payment.amount,
                            status='paid',
                        )
                        payment.method = 'wallet'
                        deducted.append((payment.user.username, payment.amount))
                    else:
                        payment.method = 'cash'
                    payment.status = 'paid'
                    payment.save(update_fields=['status', 'method'])
                elif not should_be_paid and was_paid:
                    # Reverting to pending — refund any wallet debit we made.
                    if was_wallet:
                        Wallet.objects.create(
                            user=payment.user,
                            amount=payment.amount,
                            status='refund',
                        )
                        refunded.append((payment.user.username, payment.amount))
                    payment.status = 'pending'
                    payment.save(update_fields=['status'])

        bits = [f"Payments updated for {target_session.name}"]
        if deducted:
            total = sum((amt for _, amt in deducted), Decimal('0'))
            bits.append(f"€{total} debited from {len(deducted)} wallet(s)")
        if refunded:
            total_ref = sum((amt for _, amt in refunded), Decimal('0'))
            bits.append(f"€{total_ref} refunded to {len(refunded)} wallet(s)")
        messages.success(request, ". ".join(bits) + ".")
        return redirect(f"{reverse('manage-payments')}?tab=session&session_id={target_session.id}")

    # Tab + selected session ─────────────────────────────────────
    tab = request.GET.get('tab') or 'session'
    selected_session = None
    selected_payments = []
    selected_paid_count = 0
    selected_outstanding = Decimal('0')
    selected_is_free = False
    selected_attendees = []

    # Per-user wallet balances — used by both tabs.
    wallet_by_user = {
        row['user_id']: row['balance'] or Decimal('0')
        for row in Wallet.objects.values('user_id').annotate(balance=Sum('amount'))
    }

    if tab == 'session':
        session_id = request.GET.get('session_id')
        if session_id:
            # Selectable: a confirmed paid session, or a past free session.
            selected_session = Session.objects.filter(
                models.Q(attendance_confirmed=True) | models.Q(cost__lte=0, date__lt=today),
                pk=session_id,
            ).first()
        if selected_session is None:
            selected_session = confirmed_sessions.first()

        selected_is_free = selected_session is not None and (selected_session.cost or 0) <= 0

        if selected_is_free:
            # Free session → no payments to collect. Just list the attendees with
            # their wallet balance (no cash/paid checklist).
            present_sps = (
                SessionPlayer.objects.filter(session=selected_session, attendance__attended=True)
                .select_related('user')
                .order_by('user__username')
            )
            selected_attendees = [
                {'user': sp.user, 'wallet': wallet_by_user.get(sp.user_id, Decimal('0'))}
                for sp in present_sps
            ]
        elif selected_session is not None:
            raw_payments = list(
                Payment.objects.filter(session=selected_session)
                .select_related('user')
                .order_by('user__username')
            )
            # Decorate each row with wallet info so the template can show the
            # balance chip, pre-tick players with enough credit, and preview
            # the balance after debit.
            selected_payments = []
            for p in raw_payments:
                wallet = wallet_by_user.get(p.user_id, Decimal('0'))
                covers = wallet >= p.amount
                # If already settled via wallet, the debit is in the balance.
                if p.status == 'paid' and p.method == 'wallet':
                    projected = wallet
                elif covers:
                    projected = wallet - p.amount
                else:
                    projected = wallet
                selected_payments.append({
                    'payment': p,
                    'wallet': wallet,
                    'covers': covers,
                    'projected_wallet': projected,
                })
            selected_paid_count = sum(1 for r in selected_payments if r['payment'].status == 'paid')
            selected_outstanding = sum(
                (r['payment'].amount for r in selected_payments if r['payment'].status != 'paid'),
                Decimal('0'),
            )

    # Balances tab ───────────────────────────────────────────────
    balances = []
    if tab == 'balances':
        # Aggregate per-user totals across all sessions with payments.
        payment_users = (
            Payment.objects.values('user_id')
            .annotate(
                total_due=Sum('amount'),
                outstanding=Sum('amount', filter=models.Q(status='pending')),
                paid_amount=Sum('amount', filter=models.Q(status='paid')),
            )
        )
        user_map = {u.id: u for u in User.objects.filter(payment__isnull=False).distinct()}
        for row in payment_users:
            u = user_map.get(row['user_id'])
            if u is None:
                continue
            outstanding = row['outstanding'] or Decimal('0')
            paid = row['paid_amount'] or Decimal('0')
            total = row['total_due'] or Decimal('0')
            balances.append({
                'user': u,
                'outstanding': outstanding,
                'paid': paid,
                'total': total,
                'wallet': wallet_by_user.get(u.id, Decimal('0')),
            })
        balances.sort(key=lambda b: (-b['outstanding'], b['user'].username))

    context = {
        'tab': tab,
        'confirmed_sessions': confirmed_sessions,
        'unsettled_cards': unsettled_cards,
        'settled_cards': settled_cards,
        'pending_attendance_sessions': pending_attendance_sessions,
        'free_sessions': free_sessions,
        'selected_session': selected_session,
        'selected_payments': selected_payments,
        'selected_paid_count': selected_paid_count,
        'selected_outstanding': selected_outstanding,
        'selected_is_free': selected_is_free,
        'selected_attendees': selected_attendees,
        'balances': balances,
        'outstanding_total': outstanding_total,
        'sessions_30d': sessions_30d,
        'settled_count': settled_count,
        'members_with_payments_count': members_with_payments_count,
    }
    return render(request, 'cric/pages/payments.html', context)
