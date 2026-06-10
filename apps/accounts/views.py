from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model, logout
from django.utils.decorators import method_decorator
from django.contrib.auth.views import redirect_to_login
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum, Q
from django.db.models.functions import Coalesce
from django.http import HttpResponseForbidden
from django.urls import reverse
from decimal import Decimal, InvalidOperation

from django_tables2 import SingleTableMixin
from django_filters.views import FilterView

from .models import User, PlayerProfile
from .forms import ProfileForm, EmailForm, UsernameForm, OnboardingForm, PhoneForm
from .tables import UserHTMxTable
from .filters import UserFilter

User = get_user_model()


@method_decorator(staff_member_required, name='dispatch')
class UsersHtmxTableView(SingleTableMixin, FilterView):
    model = User
    table_class = UserHTMxTable
    filterset_class = UserFilter
    template_name = "cric/pages/user_table_htmx.html"

    def get_template_names(self):
        if self.request.headers.get('HX-Request'):
            return ["cric/partials/user_table_partial.html"]
        return [self.template_name]

    def get_queryset(self):
        return super().get_queryset()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['request'] = self.request
        return context


# ─────────────────────────────────────────────────────────────────────────────
# Profile history (Games / Payments / Wallet) — read-only surfacing of data we
# already store. No new tables; each helper just queries existing rows.
# Visible to the user themselves and to staff only.
# ─────────────────────────────────────────────────────────────────────────────

HISTORY_TABS = ('games', 'payments', 'wallet')


def _games_history(user):
    """Sessions the user was rostered for, newest first, with attendance and
    their vote, plus a per-MATCH breakdown of team, result, and (when scored
    ball-by-ball) batting/bowling figures.

    Figures are keyed by match — not session — so a session with several matches
    lists each one, and every line reconciles with that match's scorecard."""
    from apps.sessions.models import SessionPlayer, Attendance
    from apps.polls.models import Vote
    from apps.matches.models import Delivery, Player

    session_players = (
        SessionPlayer.objects.filter(user=user)
        .select_related('session')
        .order_by('-session__date', '-session__time')
    )
    attended_ids = set(
        Attendance.objects.filter(match_player__user=user, attended=True)
        .values_list('match_player_id', flat=True)
    )
    votes = {
        v.poll.session_id: v.choice
        for v in Vote.objects.filter(user=user).select_related('poll')
    }

    # Per-MATCH batting / bowling from the delivery ledger.
    batting = {}   # match_id -> {runs, balls}
    for d in Delivery.objects.filter(striker__user=user).select_related('innings'):
        e = batting.setdefault(d.innings.match_id, {'runs': 0, 'balls': 0})
        e['runs'] += d.runs_off_bat
        if d.extra_type != Delivery.EXTRA_WIDE:
            e['balls'] += 1
    bowling = {}   # match_id -> {balls, runs, wkts}
    for d in Delivery.objects.filter(bowler__user=user).select_related('innings'):
        e = bowling.setdefault(d.innings.match_id, {'balls': 0, 'runs': 0, 'wkts': 0})
        if d.is_legal:
            e['balls'] += 1
        e['runs'] += d.runs_conceded
        if d.is_wicket and d.dismissal_type in Delivery.BOWLER_DISMISSALS:
            e['wkts'] += 1

    # The user's matches (one Player row per match-team), grouped by session.
    matches_by_session = {}
    player_rows = (
        Player.objects.filter(user=user)
        .select_related('team', 'team__match')
    )
    for p in player_rows:
        match = p.team.match
        if not match:
            continue
        bowl = bowling.get(match.id)
        result = None
        if match.winner_id:
            result = 'won' if match.winner_id == p.team_id else 'lost'
        matches_by_session.setdefault(match.session_id, []).append({
            'match_id': match.id,
            'name': match.name,
            'team': p.team,
            'result': result,
            'bat': batting.get(match.id),
            'bowl': {
                'overs': f"{bowl['balls'] // 6}.{bowl['balls'] % 6}",
                'runs': bowl['runs'], 'wkts': bowl['wkts'],
            } if bowl else None,
        })
    for lst in matches_by_session.values():
        lst.sort(key=lambda m: m['match_id'])  # creation order within the session

    rows = []
    for sp in session_players:
        rows.append({
            'session': sp.session,
            'attended': sp.id in attended_ids,
            'vote': votes.get(sp.session_id),
            'matches': matches_by_session.get(sp.session_id, []),
        })
    return rows


def _payments_history(user):
    """Every per-session payment, newest first, plus method/status totals.

    Includes cash payments (which never touch the wallet ledger)."""
    from apps.payments.models import Payment

    qs = (
        Payment.objects.filter(user=user)
        .select_related('session')
        .order_by('-date', '-id')
    )
    rows = list(qs)
    agg = qs.aggregate(
        paid=Sum('amount', filter=Q(status='paid')),
        pending=Sum('amount', filter=Q(status='pending')),
        wallet=Sum('amount', filter=Q(status='paid', method='wallet')),
        cash=Sum('amount', filter=Q(status='paid', method='cash')),
    )
    totals = {k: (v or Decimal('0')) for k, v in agg.items()}
    return rows, totals


_WALLET_LABELS = {
    'paid': 'Session debit',
    'refund': 'Refund',
    'adjustment': 'Staff adjustment',
    'pending': 'Top-up',
    'topup': 'Top-up',
}


def _wallet_history(user):
    """Wallet ledger rows with a running balance, newest first.

    Running balance is computed in Python (oldest→newest) to stay
    SQLite/Postgres-agnostic, then reversed for display."""
    from apps.payments.models import Wallet

    rows = list(Wallet.objects.filter(user=user).order_by('date', 'id'))
    running = Decimal('0')
    for r in rows:
        running += r.amount
        r.balance = running
        r.label = _WALLET_LABELS.get(r.status, (r.status or 'Entry').title())
        r.is_credit = r.amount >= 0
    rows.reverse()
    return rows, running


def _history_context(user, tab):
    if tab not in HISTORY_TABS:
        tab = 'games'
    ctx = {
        'profile_user': user,
        'history_tab': tab,
        'tabs': [('games', 'Games'), ('payments', 'Payments'), ('wallet', 'Wallet')],
    }
    if tab == 'payments':
        ctx['payment_rows'], ctx['payment_totals'] = _payments_history(user)
    elif tab == 'wallet':
        ctx['wallet_rows'], ctx['wallet_balance'] = _wallet_history(user)
    else:
        ctx['game_rows'] = _games_history(user)
    return ctx


@login_required
def profile_history_view(request, username, tab='games'):
    """HTMX partial for a profile's history tab. Self or staff only."""
    target = get_object_or_404(User, username=username)
    if not (request.user == target or request.user.is_staff):
        return HttpResponseForbidden("You can only view your own history.")
    return render(request, 'cric/partials/_history.html', _history_context(target, tab))


@login_required
def profile_view(request, username=None):
    if not username:
        username = request.user.username
    user = get_object_or_404(User, username=username)

    can_view_history = (request.user == user) or request.user.is_staff

    edit_mode = request.GET.get('edit', False)
    if edit_mode:
        form = ProfileForm(instance=user)
        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
        context = {'user': user, 'form': form, 'edit_mode': True, 'is_profile_page': True}
    else:
        from apps.matches import scoring
        context = {
            'user': user,
            'is_profile_page': True,
            'can_view_history': can_view_history,
            'career': scoring.career_stats(user),  # derived batting/bowling/fielding
        }
        if can_view_history:
            # Render the requested (or default Games) tab inline — no load flash.
            # ?tab= lets deep links (e.g. Member balances) land on Payments.
            context.update(_history_context(user, request.GET.get('tab', 'games')))

    return render(request, 'cric/pages/profile.html', context)


@login_required
def profile_edit_view(request):
    return redirect(f"{reverse('profile')}?edit=True")


@login_required
def profile_settings_view(request):
    return render(request, 'cric/pages/profile_settings.html', {'is_profile_page': True})


@login_required
def profile_emailchange(request):
    if request.htmx:
        if request.method == 'GET':
            form = EmailForm(instance=request.user)
            return render(request, 'partials/email_form.html', {'form': form})
        if request.method == 'POST':
            form = EmailForm(request.POST, instance=request.user)
            if form.is_valid():
                email = form.cleaned_data['email']
                if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                    messages.warning(request, f'{email} is already in use.')
                    return redirect('profile-settings')
                form.save()
                messages.success(request, 'Email updated successfully.')
                return redirect('profile-settings')
            return render(request, 'partials/email_form.html', {'form': form})

    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            form.save()
            messages.success(request, 'Email updated successfully.')
        else:
            messages.warning(request, 'Email not valid or already in use')
    return redirect('profile-settings')


@login_required
def profile_usernamechange(request):
    if request.htmx:
        if request.method == 'GET':
            form = UsernameForm(instance=request.user)
            return render(request, 'partials/username_form.html', {'form': form})
        if request.method == 'POST':
            form = UsernameForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'Username updated successfully.')
                return redirect('profile-settings')
            return render(request, 'partials/username_form.html', {'form': form})

    if request.method == 'POST':
        form = UsernameForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Username updated successfully.')
        else:
            messages.warning(request, 'Username not valid or already in use')
    return redirect('profile-settings')


@login_required
def profile_emailverify(request):
    from allauth.account.utils import send_email_confirmation
    send_email_confirmation(request, request.user)
    return redirect('profile-settings')


@login_required
def profile_phonechange(request):
    if request.htmx:
        if request.method == 'GET':
            form = PhoneForm(instance=request.user)
            return render(request, 'partials/phone_form.html', {'form': form})
        if request.method == 'POST':
            form = PhoneForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                messages.success(request, 'WhatsApp number updated.')
                return redirect('profile-settings')
            return render(request, 'partials/phone_form.html', {'form': form})

    if request.method == 'POST':
        form = PhoneForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'WhatsApp number updated.')
        else:
            messages.warning(request, 'Invalid phone number.')
    return redirect('profile-settings')


@login_required
def profile_delete_view(request):
    user = request.user
    if request.method == "POST":
        logout(request)
        user.delete()
        messages.success(request, 'Account deleted, what a pity')
        return redirect('home')
    return render(request, 'cric/pages/profile_delete.html')


@login_required
def profile_onboarding_view(request):
    # Phone is collected at signup; onboarding captures name + role + skills.
    if request.user.role:
        return redirect('home')
    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('home')
    else:
        initial_name = f"{request.user.first_name} {request.user.last_name}".strip()
        form = OnboardingForm(
            instance=request.user,
            initial={'full_name': initial_name},
        )
    return render(request, 'cric/pages/profile_onboarding.html', {'form': form})


@staff_member_required
def manage_users(request):
    if request.method == 'POST':
        user_id = request.POST.get('user_id')
        name = request.POST.get('name')
        email = request.POST.get('email')
        role = request.POST.get('role')
        is_active = request.POST.get('is_active') == 'True'
        wallet_amount = request.POST.get('wallet_amount')
        try:
            wallet_amount = Decimal(wallet_amount) if wallet_amount else Decimal('0.00')
        except (ValueError, InvalidOperation):
            wallet_amount = Decimal('0.00')

        try:
            with transaction.atomic():
                user = User.objects.get(pk=user_id)
                user.username = name
                user.email = email
                user.role = role
                user.is_active = is_active
                user.save()
                current_balance = (
                    user.wallet_set.aggregate(s=Sum('amount'))['s'] or Decimal('0')
                )
                delta = wallet_amount - current_balance
                if delta != 0:
                    user.wallet_set.create(amount=delta, status='adjustment')
            messages.success(request, "User updated successfully!")
        except User.DoesNotExist:
            messages.error(request, "User not found.")

    users = (
        User.objects.all()
        .annotate(wallet_balance=Coalesce(Sum('wallet__amount'), Decimal('0')))
        .order_by('first_name', 'username')
    )
    return render(request, 'cric/pages/manage_users.html', {'users': users})


@staff_member_required
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
                messages.success(request, f"User '{username}' deleted successfully.")
        except User.DoesNotExist:
            messages.error(request, "User not found.")
    return redirect('manage-users')


@staff_member_required
def edit_user_view(request, user_id):
    try:
        user = User.objects.get(pk=user_id)
        # Wallet balance = sum of all ledger rows for this user.
        wallet_amount = (
            user.wallet_set.aggregate(s=Sum('amount'))['s'] or Decimal('0.00')
        )

        if request.method == 'POST':
            username = request.POST.get('username')
            email = request.POST.get('email')
            role = request.POST.get('role')
            is_staff = request.POST.get('is_staff') == 'True'
            is_superuser = request.POST.get('is_superuser') == 'True'
            wallet_amount = request.POST.get('wallet_amount')
            batting_rating = request.POST.get('batting_rating')
            bowling_rating = request.POST.get('bowling_rating')
            fielding_rating = request.POST.get('fielding_rating')

            try:
                wallet_amount = Decimal(wallet_amount) if wallet_amount else Decimal('0.00')
                batting_rating = min(max(Decimal(batting_rating if batting_rating else '2.5'), Decimal('0')), Decimal('5'))
                bowling_rating = min(max(Decimal(bowling_rating if bowling_rating else '2.5'), Decimal('0')), Decimal('5'))
                fielding_rating = min(max(Decimal(fielding_rating if fielding_rating else '2.5'), Decimal('0')), Decimal('5'))
            except (ValueError, TypeError, InvalidOperation):
                wallet_amount = Decimal('0.00')
                batting_rating = Decimal('2.5')
                bowling_rating = Decimal('2.5')
                fielding_rating = Decimal('2.5')

            with transaction.atomic():
                user.username = username
                user.email = email
                user.role = role
                user.is_staff = is_staff
                user.is_superuser = is_superuser
                user.batting_rating = batting_rating
                user.bowling_rating = bowling_rating
                user.fielding_rating = fielding_rating
                user.save()

                # Wallet is a ledger: append a balancing row so Sum() lands on
                # the typed amount. Preserves the deduction/refund history.
                current_balance = (
                    user.wallet_set.aggregate(s=Sum('amount'))['s'] or Decimal('0')
                )
                delta = wallet_amount - current_balance
                if delta != 0:
                    user.wallet_set.create(amount=delta, status='adjustment')

            messages.success(request, 'User updated successfully!')
            return redirect('manage-users')

        can_delete = (user != request.user) and not user.is_superuser
        if request.headers.get('HX-Request'):
            return render(request, 'cric/partials/edit_user_form_partial.html', {
                'user': user,
                'wallet_amount': wallet_amount,
                'can_delete': can_delete,
            })
        return render(request, 'cric/pages/edit_user_form.html', {
            'user': user,
            'wallet_amount': wallet_amount,
            'modal_view': True,
            'can_delete': can_delete,
        })

    except User.DoesNotExist:
        if request.headers.get('HX-Request'):
            return render(request, 'cric/partials/edit_user_form_partial.html', {
                'message': 'User not found.',
                'success': False,
            })
        return render(request, 'cric/pages/edit_user_form.html', {
            'message': 'User not found.',
            'success': False,
        })


@login_required
def create_user_view(request):
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('manage-users')

    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        role = request.POST.get('role', 'batsman')
        is_staff = request.POST.get('is_staff') == 'on'
        is_superuser = request.POST.get('is_superuser') == 'on'
        wallet_amount = request.POST.get('wallet_amount', '0.00')

        if not username or not password:
            messages.error(request, "Username and password are required.")
            return render(request, 'cric/pages/create_user_form.html')

        if User.objects.filter(username=username).exists():
            messages.error(request, f"User '{username}' already exists.")
            return render(request, 'cric/pages/create_user_form.html', {
                'username': username, 'email': email, 'role': role,
                'is_staff': is_staff, 'is_superuser': is_superuser,
                'wallet_amount': wallet_amount,
            })

        try:
            user = User.objects.create_user(username=username, email=email, password=password)
            user.role = role
            user.is_staff = is_staff
            user.is_superuser = is_superuser
            user.save()

            try:
                amount = Decimal(wallet_amount)
                user.wallet_set.create(amount=amount)
            except (ValueError, InvalidOperation):
                user.wallet_set.create(amount=Decimal('0.00'))

            messages.success(request, f"User '{username}' created successfully!")
            return redirect('manage-users')
        except Exception as e:
            messages.error(request, f"Error creating user: {str(e)}")
            return render(request, 'cric/pages/create_user_form.html', {
                'username': username, 'email': email, 'role': role,
                'is_staff': is_staff, 'is_superuser': is_superuser,
                'wallet_amount': wallet_amount,
            })

    return render(request, 'cric/pages/create_user_form.html')
