"""Pull all scorecard data from the live DB and save to kural/scorecards.txt"""
import os, sys, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from apps.sessions.models import Session
from apps.matches.models import Match, Innings
from apps.matches import scoring

output = []

sessions = Session.objects.all().order_by('date')
for s in sessions:
    matches = s.matches.prefetch_related('teams__players__user', 'innings').all()
    if not matches.exists():
        continue
    output.append(f"\n{'='*60}")
    output.append(f"SESSION: {s.name} | {s.date} | id={s.id}")
    output.append('='*60)
    for m in matches:
        output.append(f"\n  Match: {m.name} (id={m.id})")
        teams = list(m.teams.all())
        for t in teams:
            players = [p.user.get_full_name() or p.user.username for p in t.players.select_related('user').all()]
            output.append(f"    Team '{t.name}': {', '.join(players)}")
        for inn in m.innings.order_by('number'):
            sc = scoring.innings_score(inn)
            output.append(f"\n    Innings {inn.number} — {inn.batting_team.name} batting")
            output.append(f"    Score: {sc['runs']}/{sc['wickets']} ({sc['overs']} overs) | Extras: {sc['extras']}")
            output.append(f"    {'─'*50}")
            output.append(f"    BATTING")
            for row in scoring.batting_card(inn):
                u = row['player'].user
                name = u.get_full_name() or u.username
                sr = row['strike_rate']
                status = row['how_out'] if row['out'] else 'not out'
                output.append(f"      {name:<25} {row['runs']:>4} ({row['balls']}b) 4s={row['fours']} 6s={row['sixes']} SR={sr} [{status}]")
            output.append(f"    BOWLING")
            for row in scoring.bowling_card(inn):
                u = row['player'].user
                name = u.get_full_name() or u.username
                output.append(f"      {name:<25} {row['overs']:>5} ov  {row['runs']:>3}r  {row['wickets']}w  eco={row['economy']}")

text = '\n'.join(output)
print(text)

out_path = os.path.join(os.path.dirname(__file__), '..', 'kural', 'scorecards.txt')
with open(out_path, 'w', encoding='utf-8') as f:
    f.write(text)
print(f"\n\nSaved to kural/scorecards.txt")
