from django.shortcuts import render, redirect, get_object_or_404
# redirect_to_login
from django.contrib.auth.views import redirect_to_login
from django.urls import reverse
# from allauth.account.utils import send_email_confirmation
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.db import transaction
from django.db.utils import OperationalError
from django.http import HttpResponse
from django.contrib.auth import get_user_model
from .forms import ProfileForm, EmailForm, UsernameForm, OnboardingForm
from .models import Match, Session
from django.utils import timezone


User = get_user_model()

@login_required 
def profile_view(request, username=None):
    if not username:
        username = request.user.username
    user = get_object_or_404(User, username=username)
    
    # If edit mode is requested, show the form
    edit_mode = request.GET.get('edit', False)
    if edit_mode:
        form = ProfileForm(instance=user)  # Use the user directly, not user.profile
        if request.method == 'POST':
            form = ProfileForm(request.POST, request.FILES, instance=user)
            if form.is_valid():
                form.save()
                messages.success(request, "Profile updated successfully!")
                return redirect('profile')
        context = {'user': user, 'form': form, 'edit_mode': True, 'is_profile_page': True}
    else:
        # Just display profile data
        context = {'user': user, 'is_profile_page': True}
    
    return render(request, 'cric/pages/profile.html', context)


@login_required
def profile_edit_view(request):
    # Redirect to profile with edit parameter
    return redirect(f"{reverse('profile')}?edit=True")


@login_required
def profile_settings_view(request):
    context = {'is_profile_page': True}
    return render(request, 'cric/pages/profile_settings.html', context)


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
            else:
                return render(request, 'partials/email_form.html', {'form': form})
    
    if request.method == 'POST':
        form = EmailForm(request.POST, instance=request.user)
        if form.is_valid():
            email = form.cleaned_data['email']
            if User.objects.filter(email=email).exclude(id=request.user.id).exists():
                messages.warning(request, f'{email} is already in use.')
                return redirect('profile-settings')
            
            form.save()
            # Then send confirmation email if needed
            # send_email_confirmation(request, request.user)
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
            else:
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
    send_email_confirmation(request, request.user)
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
def home_view(request):
    upcoming_sessions = Session.objects.filter(date__gte=timezone.now().date()).order_by('date', 'time')
    previous_sessions = Session.objects.filter(date__lt=timezone.now().date()).order_by('-date', '-time')
    context = {
        'upcoming_sessions': upcoming_sessions,
        'previous_sessions': previous_sessions,
    }
    return render(request, "home.html", context)

@login_required
def session_detail_view(request, session_id):
    session = get_object_or_404(Session, pk=session_id)
    # Assuming one match per session for now
    match = session.matches.first()
    
    team1_players = []
    team2_players = []
    teams = []
    if match:
        teams = match.teams.all()
        if teams.count() >= 2:
            team1_players = teams[0].players.select_related('user').all()
            team2_players = teams[1].players.select_related('user').all()

    context = {
        'session': session,
        'teams': teams,
        'team1_players': team1_players,
        'team2_players': team2_players,
    }
    return render(request, 'cric/pages/session_detail.html', context)


@login_required
def match_detail_view(request, match_id):
    match = get_object_or_404(Match, pk=match_id)
    teams = match.team_set.all()  # each match has exactly 2 teams
    if teams.count() >= 2:
        team1 = teams[0]
        team2 = teams[1]
        team1_players = team1.player_set.select_related('user').all()
        team2_players = team2.player_set.select_related('user').all()
    else:
        team1 = team2 = None
        team1_players = team2_players = []
    context = {
        'match': match,
        'team1': team1,
        'team2': team2,
        'team1_players': team1_players,
        'team2_players': team2_players,
    }
    return render(request, 'cric/pages/match_detail.html', context)

@login_required
def profile_onboarding_view(request):
    if request.user.phone:
        return redirect('profile')

    if request.method == 'POST':
        form = OnboardingForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')
    else:
        form = OnboardingForm(instance=request.user)

    return render(request, 'cric/pages/profile_onboarding.html', {'form': form})