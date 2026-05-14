from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from .models import Match, Team, Player, SessionPlayer, Attendance, Payment, Session, Poll, Vote
from django.urls import reverse
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal, InvalidOperation

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from .models import User
from .tables import UserHTMxTable
from .filters import UserFilter

User = get_user_model()


class UsersHtmxTableView(SingleTableMixin, FilterView):
    model = User
    table_class = UserHTMxTable
    filterset_class = UserFilter
    template_name = "cric/pages/user_table_htmx.html"  # Make sure this template exists

    def get_template_names(self):
        """Return appropriate template based on whether it's an HTMX request"""
        if self.request.headers.get('HX-Request'):
            return ["cric/partials/user_table_partial.html"]
        return [self.template_name]

    def get_queryset(self):
        queryset = super().get_queryset()
        # Debug output
        print(f"UsersHtmxTableView: get_queryset called")
        print(f"Filter parameters: {self.request.GET}")
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add the current request to the context
        context['request'] = self.request
        return context


@login_required
def create_session_view(request, username=None):
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
            duration = 3  # default value

        try:
            cost = float(cost)
        except (ValueError, TypeError):
            cost = 0.0  # default value

        date = None  # Initialize date and time to None
        time = None

        if not date_str:
            messages.error(request, "Date is required.")
            return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        if not time_str:
            messages.error(request, "Time is required.")
            return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(
                    request, "Invalid date format. Please use YYYY-MM-DD.")
                return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        if time_str:
            try:
                time = timezone.datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                messages.error(
                    request, "Invalid time format. Please use HH:MM.")
                return render(request, 'cric/pages/create_session.html', {'users': User.objects.all()})

        # Create the Session
        session = Session.objects.create(
            name=name,
            date=date,
            time=time,
            duration=duration,
            location=location,
            cost=cost,
            created_by=request.user
        )

        # Create a default poll for the session
        poll = Poll.objects.create(
            session=session,
            question="Will you attend this session?",
            is_open=True
        )

        messages.success(request, 'Session created successfully!')
        return redirect('home')
    else:
        all_users = User.objects.all()
        context = {
            'users': all_users,
        }
        return render(request, 'cric/pages/create_session.html', context)


@login_required
def attendance_view(request):
    # This view will now only list the matches.
    all_matches = Match.objects.filter(session__isnull=False).select_related(
        'session').order_by('-session__date', '-session__time')

    # Calculate and attach dynamic info for all matches
    for match in all_matches:
        attended_mps = Attendance.objects.filter(
            match_player__session=match.session, attended=True)
        count = attended_mps.count()
        cost = None
        if match.session and match.session.attendance_confirmed and match.session.cost_per_person:
            cost = match.session.cost_per_person
        elif count > 0 and match.session and match.session.cost > 0:
            cost = round(match.session.cost / Decimal(count), 2)

        match.attended_count = count
        match.cost_per_person_calculated = cost

    context = {
        'matches': all_matches,
    }
    return render(request, 'cric/pages/attendance_list.html', context)


@login_required
def match_attendance_detail_view(request, match_id):
    try:
        match = Match.objects.prefetch_related(
            'teams__captain').get(pk=match_id)
        session = match.session
    except Match.DoesNotExist:
        messages.error(request, "The selected match does not exist.")
        return redirect('attendance_list')

    # POST request handling (saving changes)
    if request.method == 'POST':
        present_mp_ids = request.POST.getlist('present')

        # Update attendance records for all players in the session
        for mp in SessionPlayer.objects.filter(session=session):
            attendance, created = Attendance.objects.get_or_create(
                match_player=mp)
            attendance.attended = str(mp.id) in present_mp_ids
            attendance.save()

        messages.success(
            request, f'Attendance for "{match.name}" updated successfully!')

        # Handle attendance confirmation and cost calculation
        if 'confirm_attendance' in request.POST:
            present_count = len(present_mp_ids)
            session = match.session
            if session:
                if present_count > 0 and session.cost > 0:
                    cost_per_person = session.cost / Decimal(present_count)
                    session.cost_per_person = round(cost_per_person, 2)
                    session.attendance_confirmed = True
                    session.save()
                    messages.success(
                        request, f'Attendance confirmed for {present_count} players. Cost per person is {session.cost_per_person}.')
                else:
                    # Reset if no one is present or cost is zero
                    session.cost_per_person = None
                    session.attendance_confirmed = False
                    session.save()
                    messages.warning(
                        request, 'Attendance confirmation reset (no players or no cost).')

        return redirect('match_attendance_detail', match_id=match.id)

    # GET request handling (displaying the page)
    teams = match.teams.all()
    team1_players = []
    team2_players = []
    if teams.count() >= 2:
        team1 = teams[0]
        team2 = teams[1]
        team1_players = SessionPlayer.objects.filter(
            session=session, team=team1).select_related('user').all()
        team2_players = SessionPlayer.objects.filter(
            session=session, team=team2).select_related('user').all()

    present_list = list(Attendance.objects.filter(
        match_player__session=session, attended=True).values_list('match_player_id', flat=True))

    context = {
        'match': match,
        'teams': teams,
        'team1_players': team1_players,
        'team2_players': team2_players,
        'present_list': present_list,
    }
    return render(request, 'cric/pages/attendance_detail.html', context)


@login_required
def payments_view(request):
    sessions = Session.objects.all()
    selected_session = None
    teams = []
    if request.method == 'POST':
        session_id = request.POST.get('session_id')
        try:
            selected_session = Session.objects.get(pk=session_id)
            match = selected_session.matches.first()
            if match:
                teams = list(match.team_set.all())

        except Session.DoesNotExist:
            messages.error(request, 'Session not found!')
    elif 'session_id' in request.GET:
        session_id = request.GET.get('session_id')
        try:
            selected_session = Session.objects.get(pk=session_id)
            match = selected_session.matches.first()
            if match:
                teams = list(match.team_set.all())
        except Session.DoesNotExist:
            selected_session = None

    # Build dictionary mapping attended players (user.id -> attendance record)
    attendance_by_player = {}
    if selected_session:
        for attendance in Attendance.objects.filter(match_player__session=selected_session, attended=True):
            attendance_by_player[attendance.match_player.user.id] = attendance

    # Build list of player ids with payment status "paid"
    paid_list = []
    if selected_session:
        for payment in Payment.objects.filter(session=selected_session, status='paid'):
            # Find the session player associated with this user
            session_player = SessionPlayer.objects.filter(
                session=selected_session, user=payment.user).first()
            if session_player:
                paid_list.append(str(session_player.id))

    context = {
        'sessions': sessions,
        'selected_session': selected_session,
        'teams': teams,
        'paid_list': paid_list,
        'attendance_by_player': attendance_by_player,
    }
    return render(request, 'cric/pages/payments.html', context)


@login_required
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'True'
        wallet_amount = request.POST.get('wallet_amount')
        try:
            wallet_amount = Decimal(
                wallet_amount) if wallet_amount else Decimal('0.00')
        except:
            wallet_amount = Decimal('0.00')

        try:
            user = User.objects.get(pk=user_id)
            user.username = name
            user.email = email
            user.role = role
            user.is_active = is_active
            user.save()

            # Update or create Wallet record
            wallet = user.wallet_set.first()
            if wallet:
                wallet.amount = wallet_amount
                wallet.save()
            else:
                user.wallet_set.create(amount=wallet_amount)

            messages.success(request, "User updated successfully!")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    users = User.objects.all().order_by('first_name', 'username')
    context = {'users': users}
    # Explicitly specify the full template path to ensure consistency
    return render(request, 'cric/pages/manage_users.html', context)


@login_required
def delete_user_view(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(pk=user_id)
            if user == request.user:
                messages.error(request, "You cannot delete your own account.")
            elif user.is_superuser:
                messages.error(request, "Cannot delete admin accounts.")
            else:
                username = user.get_full_name() or user.username
                user.delete()
                messages.success(
                    request, f"User '{username}' deleted successfully.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('cric:manage-users')


@login_required
def edit_user_view(request, user_id):
    """View for editing user details via modal form."""
    try:
        user = User.objects.get(pk=user_id)
        wallet = user.wallet_set.first()
        wallet_amount = wallet.amount if wallet else 0.00

        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            is_staff = request.POST.get('is_staff') == 'True'
            is_superuser = request.POST.get(
                'is_superuser') == 'True'  # Add admin checkbox
            wallet_amount = request.POST.get('wallet_amount')

            # Get rating values
            batting_rating = request.POST.get('batting_rating')
            bowling_rating = request.POST.get('bowling_rating')
            fielding_rating = request.POST.get('fielding_rating')

            # Process data and update the user
            try:
                wallet_amount = Decimal(
                    wallet_amount) if wallet_amount else Decimal('0.00')

                # Convert ratings to Decimal with valid bounds (0-5)
                batting_rating = min(max(Decimal(
                    batting_rating if batting_rating else '2.5'), Decimal('0')), Decimal('5'))
                bowling_rating = min(max(Decimal(
                    bowling_rating if bowling_rating else '2.5'), Decimal('0')), Decimal('5'))
                fielding_rating = min(max(Decimal(
                    fielding_rating if fielding_rating else '2.5'), Decimal('0')), Decimal('5'))
            except (ValueError, TypeError, InvalidOperation):
                wallet_amount = Decimal('0.00')
                batting_rating = Decimal('2.5')
                bowling_rating = Decimal('2.5')
                fielding_rating = Decimal('2.5')

            # Update user data
            user.username = username
            user.email = email
            user.role = role
            user.is_staff = is_staff
            user.is_superuser = is_superuser  # Save admin status

            # Update ratings
            user.batting_rating = batting_rating
            user.bowling_rating = bowling_rating
            user.fielding_rating = fielding_rating

            user.save()

            # Update or create Wallet record
            if wallet:
                wallet.amount = wallet_amount
                wallet.save()
            else:
                user.wallet_set.create(amount=wallet_amount)

            messages.success(request, 'User updated successfully!')
            # Always redirect to the namespaced URL to ensure consistent UI
            return redirect('cric:manage-users')

        # Check if this is an HTMX request (for modal/popup view)
        if request.headers.get('HX-Request'):
            # For HTMX requests, use a partial template without header/footer
            return render(request, 'cric/partials/edit_user_form_partial.html', {
                'user': user,
                'wallet_amount': wallet_amount
            })

        # For regular requests, use the full page template
        return render(request, 'cric/pages/edit_user_form.html', {
            'user': user,
            'wallet_amount': wallet_amount,
            'modal_view': True  # Flag to indicate this should be rendered as a modal
        })

    except User.DoesNotExist:
        if request.headers.get('HX-Request'):
            return render(request, 'cric/partials/edit_user_form_partial.html', {
                'message': 'User not found.',
                'success': False
            })
        return render(request, 'cric/pages/edit_user_form.html', {
            'message': 'User not found.',
            'success': False
        })


@login_required
def session_detail_view(request, session_id):
    session = get_object_or_404(Session, id=session_id)

    # Poll info
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
        yes_voters = [{'user': v.user, 'team_assigned': False}
                      for v in poll.votes.filter(choice='yes').select_related('user')]
        no_voters = [v.user for v in poll.votes.filter(choice='no').select_related('user')]

    # All matches
    matches = list(session.matches.prefetch_related('teams__players__user').order_by('id'))

    # Edit match from query string
    edit_match_id = request.GET.get('edit_match')
    edit_match = edit_team1 = edit_team2 = None
    edit_team1_players = []
    edit_team2_players = []

    if edit_match_id:
        edit_match = get_object_or_404(Match, id=edit_match_id, session=session)
        teams = list(edit_match.teams.order_by('id'))
        if len(teams) >= 1:
            edit_team1 = teams[0]
            edit_team1_players = list(edit_team1.players.select_related('user').all())
        if len(teams) >= 2:
            edit_team2 = teams[1]
            edit_team2_players = list(edit_team2.players.select_related('user').all())

    # Mark yes voters as assigned if they're in the edit match's teams
    assigned_ids = {p.user.id for p in edit_team1_players + edit_team2_players}
    for voter in yes_voters:
        voter['team_assigned'] = voter['user'].id in assigned_ids

    context = {
        'session': session,
        'user_vote': user_vote,
        'yes_votes': yes_votes,
        'no_votes': no_votes,
        'total_votes': total_votes,
        'yes_percentage': yes_percentage,
        'yes_voters': yes_voters,
        'no_voters': no_voters,
        'matches': matches,
        'edit_match': edit_match,
        'edit_team1': edit_team1,
        'edit_team2': edit_team2,
        'edit_team1_players': edit_team1_players,
        'edit_team2_players': edit_team2_players,
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

        choice = request.POST.get('choice')
        if choice in ['yes', 'no']:
            Vote.objects.update_or_create(
                poll=poll,
                user=request.user,
                defaults={'choice': choice}
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
        messages.error(
            request, "You don't have permission to perform this action.")
        return redirect('home')

    poll = get_object_or_404(Poll, id=poll_id)
    session = poll.session

    if request.method == 'POST':
        poll.is_open = not poll.is_open
        poll.save()
        status = "opened" if poll.is_open else "closed"
        messages.success(request, f"Poll has been {status}.")

    return redirect('session_detail', session_id=session.id)


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
            match_number = session.matches.count() + 1
            match = Match.objects.create(
                session=session,
                name=match_name or f"Match {match_number}"
            )

        # Delete existing teams for this match only (cascades to Player)
        match.teams.all().delete()

        # Team 1
        team1_captain = User.objects.filter(id=team1_captain_id).first() if team1_captain_id else None
        team1 = Team.objects.create(match=match, name=team1_name, captain=team1_captain)
        for pid in team1_ids:
            try:
                u = User.objects.get(id=int(pid))
                Player.objects.create(user=u, team=team1, role=u.role)
            except (User.DoesNotExist, ValueError):
                pass

        # Team 2
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

    if request.method == 'POST':
        last_match = session.matches.order_by('-id').first()
        match_number = session.matches.count() + 1
        new_match = Match.objects.create(
            session=session,
            name=f"Match {match_number}"
        )
        # Copy teams from last match
        if last_match:
            for old_team in last_match.teams.order_by('id'):
                new_team = Team.objects.create(
                    match=new_match,
                    name=old_team.name,
                    captain=old_team.captain
                )
                for old_player in old_team.players.select_related('user').all():
                    Player.objects.create(
                        user=old_player.user,
                        team=new_team,
                        role=old_player.role
                    )
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
        match.delete()
        messages.success(request, f"{match.name} deleted.")

    return redirect('session_detail', session_id=session_id)


@login_required
def create_user_view(request):
    """View for creating a new user."""
    if not request.user.is_staff:
        messages.error(
            request, "You don't have permission to perform this action.")
        return redirect('cric:manage-users')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'batsman')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        wallet_amount = request.POST.get('wallet_amount', '0.00')

        # Validate inputs
        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'cric/pages/create_user_form.html')

        # Check if user already exists
        if User.objects.filter(username=username).exists():
            messages.error(request, f"User '{username}' already exists.")
            return render(request, 'cric/pages/create_user_form.html', {
                'username': username,
                'email': email,
                'role': role,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
                'wallet_amount': wallet_amount
            })

        try:
            # Create new user
            user = User.objects.create_user(
                username=username,
                email=email,
                password=password
            )
            user.role = role
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            # Create wallet if amount provided
            try:
                amount = Decimal(wallet_amount)
                user.wallet_set.create(amount=amount)
            except (ValueError, InvalidOperation):
                user.wallet_set.create(amount=Decimal('0.00'))

            messages.success(
                request, f"User '{username}' created successfully!")

            # Always use the namespaced URL for redirection to ensure consistent UI
            return redirect('cric:manage-users')
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return render(request, 'cric/pages/create_user_form.html', {
                'username': username,
                'email': email,
                'role': role,
                'is_staff': is_staff,
                'is_superuser': is_superuser,
                'wallet_amount': wallet_amount
            })

    # GET request - show the form
    return render(request, 'cric/pages/create_user_form.html')


@login_required
def delete_session_view(request, session_id):
    """View for deleting a session (admin only)."""
    if not request.user.is_staff:
        messages.error(
            request, "You don't have permission to perform this action.")
        return redirect('home')

    session = get_object_or_404(Session, id=session_id)

    if request.method == 'POST':
        # Store session name to use in success message
        session_name = session.name

        # Delete the session (this will cascade delete related objects)
        session.delete()

        messages.success(
            request, f"Session '{session_name}' has been deleted.")
        return redirect('home')

    # If it's a GET request, redirect to session detail
    return redirect('session_detail', session_id=session_id)


def home(request):
    """Home page view showing upcoming and previous sessions."""
    today = timezone.now().date()

    # Get upcoming sessions (today or future dates)
    upcoming_sessions = Session.objects.filter(
        date__gte=today).order_by('date', 'time')

    # Get previous sessions (past dates)
    previous_sessions = Session.objects.filter(date__lt=today).order_by(
        '-date', '-time')[:10]  # Limit to 10 recent sessions

    # Calculate vote counts for each session
    session_vote_counts = {}
    for session in list(upcoming_sessions) + list(previous_sessions):
        if hasattr(session, 'poll'):
            yes_votes = session.poll.votes.filter(choice='yes').count()
            no_votes = session.poll.votes.filter(choice='no').count()
            total_votes = yes_votes + no_votes
            yes_percentage = (yes_votes / total_votes *
                              100) if total_votes > 0 else 0

            session_vote_counts[session.id] = {
                'yes_votes': yes_votes,
                'no_votes': no_votes,
                'total_votes': total_votes,
                'yes_percentage': yes_percentage
            }

    context = {
        'upcoming_sessions': upcoming_sessions,
        'previous_sessions': previous_sessions,
        'vote_counts': session_vote_counts
    }
    return render(request, 'home.html', context)
