from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import get_user_model
from cric_users.models import Match, Team, Player, Attendance, Payment
from django.utils import timezone
from django.contrib import messages
from decimal import Decimal

User = get_user_model()

@login_required
def create_match_view(request, username=None):
    if request.method == 'POST':
        name = request.POST['name']
        date_str = request.POST['date']
        time_str = request.POST['time']
        duration = int(request.POST['duration'])
        location = request.POST['location']
        cost = float(request.POST['cost'])
        team1_players = request.POST.getlist('team1_players')
        team2_players = request.POST.getlist('team2_players')

        #make the ids string to list of ints
        team1_players = [int(i) for i in team1_players[0].split(',')]
        team2_players = [int(i) for i in team2_players[0].split(',')]
        
        date = None  # Initialize date and time to None
        time = None

        if date_str:
            try:
                date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                messages.error(request, "Invalid date format. Please use YYYY-MM-DD.")
                return render(request, 'cric_manage/create_match.html', {'users': User.objects.all()})  # Re-render the form with an error message

        if time_str:
            try:
                time = timezone.datetime.strptime(time_str, '%H:%M').time()
            except ValueError:
                messages.error(request, "Invalid time format. Please use HH:MM.")
                return render(request, 'cric_manage/create_match.html', {'users': User.objects.all()})  # Re-render the form with an error message
        

        team1_captain = None
        team2_captain = None

        if team1_players:
             team1_captain = User.objects.get(pk=team1_players[0])
        if team2_players:
            team2_captain = User.objects.get(pk=team2_players[0])

        # First create the Match
        match = Match.objects.create(
            name=name,
            date=date,
            time=time,
            duration=duration,
            location=location,
            cost=cost,
        )

        # Then create the Teams, associating them with the Match
        team1 = Team.objects.create(match=match, name='Team 1', captain=team1_captain)
        team2 = Team.objects.create(match=match, name='Team 2', captain=team2_captain)

        # Create players for Team 1
        team1_player_ids = [uid for uid in team1_players if uid]  # Filter out empty strings
        for user_id in team1_player_ids:
            user = User.objects.get(pk=user_id)
            Player.objects.create(team=team1, user=user, role=user.role)

        # Create players for Team 2
        team2_player_ids =  [uid for uid in team2_players if uid]
        for user_id in team2_player_ids:
            user = User.objects.get(pk=user_id)
            Player.objects.create(team=team2, user=user, role=user.role)

        messages.success(request, 'Match created successfully!')
        return redirect('home')
    else:
        all_users = User.objects.all()
        context = {
            'users': all_users,
        }
        return render(request, 'cric_manage/create_match.html', context)

@login_required
def attendance_view(request):
    matches = Match.objects.all()
    selected_match = None
    teams = []
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        try:
            selected_match = Match.objects.get(pk=match_id)
            teams = list(selected_match.team_set.all())
            present_ids = request.POST.getlist('present')
            for team in teams:
                for player in team.player_set.all():
                    att, created = Attendance.objects.get_or_create(match=selected_match, player=player)
                    att.attended = str(player.id) in present_ids
                    att.save()
            messages.success(request, 'Attendance updated successfully!')
            # If confirming attendance, calculate cost per person.
            if 'confirm_attendance' in request.POST:
                attended_count = 0
                for team in teams:
                    for player in team.player_set.all():
                        try:
                            if Attendance.objects.get(match=selected_match, player=player).attended:
                                attended_count += 1
                        except Attendance.DoesNotExist:
                            pass
                if attended_count:
                    selected_match.cost_per_person = round(selected_match.cost / attended_count, 2)
                    selected_match.attendance_confirmed = True
                    selected_match.save()
                    messages.success(request, 'Attendance confirmed and cost per person updated!')
                else:
                    messages.error(request, 'No players attended to confirm.')
        except Match.DoesNotExist:
            messages.error(request, 'Match not found!')
    elif 'match_id' in request.GET:
        match_id = request.GET.get('match_id')
        try:
            selected_match = Match.objects.get(pk=match_id)
            teams = list(selected_match.team_set.all())
        except Match.DoesNotExist:
            selected_match = None

    # Build list of player ids with attendance marked true.
    present_list = []
    if selected_match:
        for team in teams:
            for player in team.player_set.all():
                try:
                    record = Attendance.objects.get(match=selected_match, player=player)
                    if record.attended:
                        present_list.append(player.id)
                except Attendance.DoesNotExist:
                    pass

    dynamic_cost_per_person = None
    if selected_match and present_list:
        dynamic_cost_per_person = round(selected_match.cost / len(present_list), 2)
    
    dynamic_count = len(present_list) if selected_match else 0
    confirmed_count = dynamic_count if selected_match and selected_match.attendance_confirmed else None

    dynamic_info = {}
    for m in matches:
        records = Attendance.objects.filter(match=m, attended=True)
        count = records.count()
        cost = round(m.cost / count, 2) if count else None
        dynamic_info[str(m.id)] = {'count': count, 'cost': cost}

    context = {
        'matches': matches,
        'selected_match': selected_match,
        'teams': teams,
        'present_list': present_list,
        'dynamic_cost_per_person': dynamic_cost_per_person,
        'dynamic_count': dynamic_count,
        'confirmed_count': confirmed_count,
        'dynamic_info': dynamic_info,
    }
    return render(request, 'cric_manage/attendance.html', context)

@login_required
def payments_view(request):
    matches = Match.objects.all()
    selected_match = None
    teams = []
    if request.method == 'POST':
        match_id = request.POST.get('match_id')
        try:
            selected_match = Match.objects.get(pk=match_id)
            teams = list(selected_match.team_set.all())
            paid_ids = request.POST.getlist('paid')
            for team in teams:
                for player in team.player_set.all():
                    try:
                        attendance = Attendance.objects.get(match=selected_match, player=player)
                        if attendance.attended:
                            payment, created = Payment.objects.get_or_create(
                                user=player.user, match=selected_match,
                                defaults={
                                    'amount': (selected_match.cost_per_person if selected_match.attendance_confirmed else selected_match.cost)
                                }
                            )
                            payment.status = 'paid' if str(player.id) in paid_ids else 'pending'
                            payment.save()
                    except Attendance.DoesNotExist:
                        pass
            messages.success(request, 'Payments updated successfully!')
        except Match.DoesNotExist:
            messages.error(request, 'Match not found!')
    elif 'match_id' in request.GET:
        match_id = request.GET.get('match_id')
        try:
            selected_match = Match.objects.get(pk=match_id)
            teams = list(selected_match.team_set.all())
        except Match.DoesNotExist:
            selected_match = None

    # Build dictionary mapping attended players (player.id -> attendance record)
    attendance_by_player = {}
    if selected_match:
        for team in teams:
            for player in team.player_set.all():
                try:
                    record = Attendance.objects.get(match=selected_match, player=player)
                    if record.attended:
                        attendance_by_player[player.id] = record
                except Attendance.DoesNotExist:
                    pass

    # Build list of player ids with payment status "paid"
    paid_list = []
    if selected_match:
        for team in teams:
            for player in team.player_set.all():
                try:
                    payment = Payment.objects.get(user=player.user, match=selected_match)
                    if payment.status == 'paid':
                        paid_list.append(player.id)
                except Payment.DoesNotExist:
                    pass

    context = {
        'matches': matches,
        'selected_match': selected_match,
        'teams': teams,
        'paid_list': paid_list,
        'attendance_by_player': attendance_by_player,
    }
    return render(request, 'cric_manage/payments.html', context)


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
            wallet_amount = Decimal(wallet_amount) if wallet_amount else Decimal('0.00')
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
            
    users = User.objects.all()
    context = {'users': users}
    return render(request, 'cric_manage/manage_users.html', context)
