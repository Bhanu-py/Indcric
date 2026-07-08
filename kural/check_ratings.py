"""Check player ratings and simulate balanced team split.

Run with live DB env var set to see real ratings, or without to use local data.

Usage:
    python -m kural.check_ratings
    python -m kural.check_ratings --session 20   # split based on who attended session 20
"""
from django.contrib.auth import get_user_model
from decimal import Decimal
import os
import sys
import django
import argparse
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

User = get_user_model()


# ── Team balancing algorithm ──────────────────────────────────────────────────

def get_skills(u):
    return (
        float(u.batting_rating or 0),
        float(u.bowling_rating or 0),
        float(u.fielding_rating or 0),
    )


def combined_rating(u):
    bat, bowl, fld = get_skills(u)
    return round((bat + bowl + fld) / 3, 2)


def team_totals(team):
    bat = sum(get_skills(u)[0] for u in team)
    bowl = sum(get_skills(u)[1] for u in team)
    fld = sum(get_skills(u)[2] for u in team)
    return bat, bowl, fld


def imbalance(team_a, team_b):
    a = team_totals(team_a)
    b = team_totals(team_b)
    return sum((ai - bi) ** 2 for ai, bi in zip(a, b))


def balance_teams(players):
    """Snake draft + iterative swap improvement across batting/bowling/fielding."""
    sorted_p = sorted(players, key=lambda u: sum(get_skills(u)), reverse=True)
    team_a, team_b = [], []
    for i, p in enumerate(sorted_p):
        (team_a if i % 4 in (0, 3) else team_b).append(p)

    improved = True
    while improved:
        improved = False
        best = imbalance(team_a, team_b)
        best_swap = None
        for i in range(len(team_a)):
            for j in range(len(team_b)):
                new_a = team_a[:i] + [team_b[j]] + team_a[i+1:]
                new_b = team_b[:j] + [team_a[i]] + team_b[j+1:]
                score = imbalance(new_a, new_b)
                if score < best:
                    best, best_swap = score, (i, j)
        if best_swap:
            i, j = best_swap
            team_a[i], team_b[j] = team_b[j], team_a[i]
            improved = True
    return team_a, team_b


# ── Main ──────────────────────────────────────────────────────────────────────

parser = argparse.ArgumentParser()
parser.add_argument('--session', type=int, default=None,
                    help='Use players from a specific session ID')
args = parser.parse_args()

print("\n" + "="*65)
print("PLAYER RATINGS (from DB)")
print("="*65)
print(f"{'Username':<25} {'Batting':>7} {'Bowling':>7} {'Fielding':>8} {'Combined':>9}")
print("-"*65)

if args.session:
    from apps.sessions.models import SessionPlayer
    session_players = (
        SessionPlayer.objects.filter(session_id=args.session)
        .select_related('user')
        .order_by('-user__batting_rating')
    )
    players = [sp.user for sp in session_players]
    print(
        f"  (Filtered to session id={args.session} — {len(players)} players)\n")
else:
    players = list(
        User.objects.filter(is_active=True)
        .exclude(username__startswith='test_')
        .exclude(username__startswith='Un_registered')
        .order_by('-batting_rating')
    )

for u in players:
    bat = float(u.batting_rating or 0)
    bowl = float(u.bowling_rating or 0)
    fld = float(u.fielding_rating or 0)
    comb = combined_rating(u)
    name = u.get_full_name() or u.username
    print(f"  {name:<23} {bat:>7.1f} {bowl:>7.1f} {fld:>8.1f} {comb:>9.2f}")

# ── Check conditions ──────────────────────────────────────────────────────────
print("\n" + "="*65)
print("CONDITIONS CHECK")
print("="*65)

all_rated = [u for u in players if any([
    u.batting_rating and u.batting_rating > 0,
    u.bowling_rating and u.bowling_rating > 0,
    u.fielding_rating and u.fielding_rating > 0,
])]
unrated = [u for u in players if u not in all_rated]

print(f"  Players with ratings:    {len(all_rated)}")
print(f"  Players with all zeros:  {len(unrated)}")
if unrated:
    names = ', '.join(u.get_full_name() or u.username for u in unrated)
    print(f"    → {names}")
    print(f"    ⚠ These players have no match history yet — rated 0.")

# ── Team split simulation ─────────────────────────────────────────────────────
split_pool = all_rated if all_rated else players

print("\n" + "="*65)
print(f"SIMULATED TEAM SPLIT ({len(split_pool)} players)")
print("="*65)

team_a, team_b = balance_teams(split_pool)
a_bat, a_bowl, a_fld = team_totals(team_a)
b_bat, b_bowl, b_fld = team_totals(team_b)


def _verdict(diff, label):
    icon = "✓" if diff <= 0.5 else ("~" if diff <= 1.0 else "✗")
    return f"  {icon} {label} diff: {diff:.2f}"


print(f"\n  Team A ({len(team_a)} players)")
print(f"  {'Name':<28} {'Bat':>5} {'Bowl':>6} {'Fld':>6}")
print("  " + "─"*48)
for u in sorted(team_a, key=lambda u: sum(get_skills(u)), reverse=True):
    bat, bowl, fld = get_skills(u)
    print(
        f"  {(u.get_full_name() or u.username):<28} {bat:>5.1f} {bowl:>6.1f} {fld:>6.1f}")
print(f"  {'TOTAL':<28} {a_bat:>5.1f} {a_bowl:>6.1f} {a_fld:>6.1f}")

print(f"\n  Team B ({len(team_b)} players)")
print(f"  {'Name':<28} {'Bat':>5} {'Bowl':>6} {'Fld':>6}")
print("  " + "─"*48)
for u in sorted(team_b, key=lambda u: sum(get_skills(u)), reverse=True):
    bat, bowl, fld = get_skills(u)
    print(
        f"  {(u.get_full_name() or u.username):<28} {bat:>5.1f} {bowl:>6.1f} {fld:>6.1f}")
print(f"  {'TOTAL':<28} {b_bat:>5.1f} {b_bowl:>6.1f} {b_fld:>6.1f}")

print(f"\n  Balance check:")
print(_verdict(abs(a_bat - b_bat),  "Batting "))
print(_verdict(abs(a_bowl - b_bowl), "Bowling "))
print(_verdict(abs(a_fld - b_fld),  "Fielding"))
print()
