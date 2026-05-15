from django.shortcuts import render, get_object_or_404
from .models import Match


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
