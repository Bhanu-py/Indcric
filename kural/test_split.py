"""Test exact team splitting for the players from the current session screenshot.

Players: ashok_kumar, bhanu, mani_kaarthik, Niranjan, Sathish, tc,
         Koushal_kumar, PremKRaghupathi, Ramuhaky, Shobin, Akhil_Reddy, Aru, kuralarasan
"""
import os
import sys
from itertools import combinations
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "cric_core.settings")

import django

django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

# IDs from players.md
PLAYER_IDS = [31, 1, 60, 28, 43, 49, 41, 22, 30, 48, 15, 35, 14]


def get_skills(user):
    return (
        float(user.batting_rating if user.batting_rating is not None else 2.5),
        float(user.bowling_rating if user.bowling_rating is not None else 2.5),
        float(user.fielding_rating if user.fielding_rating is not None else 2.5),
    )


def combined_rating(user):
    return sum(get_skills(user)) / 3


def player_strength(user):
    bat, bowl, field = get_skills(user)
    return (combined_rating(user) * 2) + bat + bowl + field


def role_bucket(user):
    role = (user.role or "").lower()
    if role in ("bowler", "bowling"):
        return "bowler"
    if role in ("allrounder", "all-rounder"):
        return "allrounder"
    if role in ("keeper", "wicketkeeper"):
        return "keeper"
    if role in ("batsman", "batter", "batting"):
        return "batsman"
    return "other"


def team_totals(team):
    bat = sum(get_skills(user)[0] for user in team)
    bowl = sum(get_skills(user)[1] for user in team)
    field = sum(get_skills(user)[2] for user in team)
    return bat, bowl, field


def mean_gap(team_a, team_b, skill_index):
    if not team_a or not team_b:
        return 0
    return abs(
        sum(get_skills(user)[skill_index] for user in team_a) / len(team_a)
        - sum(get_skills(user)[skill_index] for user in team_b) / len(team_b)
    )


def role_gap(team_a, team_b):
    weights = {
        "bowler": 0.35,
        "allrounder": 0.25,
        "keeper": 0.20,
        "batsman": 0.15,
        "other": 0.10,
    }
    score = 0
    for role, weight in weights.items():
        a_count = sum(1 for user in team_a if role_bucket(user) == role)
        b_count = sum(1 for user in team_b if role_bucket(user) == role)
        score += abs(a_count - b_count) * weight
    return score


def split_score(team_a, team_b, top_player_ids):
    batting_gap = mean_gap(team_a, team_b, 0)
    bowling_gap = mean_gap(team_a, team_b, 1)
    fielding_gap = mean_gap(team_a, team_b, 2)
    rating_gap = abs(
        sum(combined_rating(user) for user in team_a) / len(team_a)
        - sum(combined_rating(user) for user in team_b) / len(team_b)
    )
    top_gap = abs(
        sum(1 for user in team_a if user.id in top_player_ids)
        - sum(1 for user in team_b if user.id in top_player_ids)
    ) * 0.25
    total_rating_gap = abs(
        sum(combined_rating(user) for user in team_a)
        - sum(combined_rating(user) for user in team_b)
    ) * 0.03
    return (
        batting_gap * 3
        + bowling_gap * 3
        + fielding_gap * 2
        + rating_gap * 2
        + role_gap(team_a, team_b)
        + top_gap
        + total_rating_gap
    )


def balance_teams_3d(players):
    """Exact balanced partition search across batting, bowling, and fielding."""
    ordered = sorted(
        players,
        key=lambda user: (player_strength(user), user.get_full_name() or user.username),
        reverse=True,
    )
    if len(ordered) < 2:
        return ordered, []

    top_count = max(2, (len(ordered) + 3) // 4)
    top_player_ids = {user.id for user in ordered[:top_count]}
    target_sizes = sorted({len(ordered) // 2, (len(ordered) + 1) // 2})

    best_score = float("inf")
    best_team_a_ids = set()

    for target_size in target_sizes:
        for team_a_tuple in combinations(ordered, target_size):
            team_a = list(team_a_tuple)
            team_a_ids = {user.id for user in team_a}
            team_b = [user for user in ordered if user.id not in team_a_ids]
            score = split_score(team_a, team_b, top_player_ids)
            if score < best_score:
                best_score = score
                best_team_a_ids = team_a_ids

    return (
        [user for user in ordered if user.id in best_team_a_ids],
        [user for user in ordered if user.id not in best_team_a_ids],
    )


def verdict(diff, label):
    icon = "✓" if diff <= 0.5 else ("~" if diff <= 1.0 else "✗")
    return f"  {icon} {label} diff: {diff:.2f}"


def print_team(name, team):
    bat, bowl, field = team_totals(team)
    print(f"\n  {name} ({len(team)} players)")
    print(f"  {'Name':<28} {'Bat':>5} {'Bowl':>6} {'Fld':>6} {'Role':>12}")
    print("  " + "─" * 62)
    for user in sorted(team, key=player_strength, reverse=True):
        display_name = user.get_full_name() or user.username
        user_bat, user_bowl, user_field = get_skills(user)
        print(
            f"  {display_name:<28} {user_bat:>5.1f} {user_bowl:>6.1f} "
            f"{user_field:>6.1f} {role_bucket(user):>12}"
        )
    print(f"  {'TOTAL':<28} {bat:>5.1f} {bowl:>6.1f} {field:>6.1f}")


def main():
    players = list(
        User.objects.filter(id__in=PLAYER_IDS)
        .order_by("first_name", "username")
    )
    found_ids = {user.id for user in players}
    missing_ids = [player_id for player_id in PLAYER_IDS if player_id not in found_ids]

    print("\n" + "=" * 68)
    print("PLAYER RATINGS (A–Z)")
    print("=" * 68)
    if missing_ids:
        print(f"  Missing IDs in this database: {missing_ids}")
        print(f"  Found {len(players)} of {len(PLAYER_IDS)} configured players.")
        print()
    print(f"  {'Name':<28} {'Bat':>5} {'Bowl':>6} {'Fld':>6} {'Role':>12}")
    print("  " + "─" * 62)
    for user in players:
        display_name = user.get_full_name() or user.username
        bat, bowl, field = get_skills(user)
        flag = "  ← no history" if bat == bowl == field == 2.5 else ""
        flag = "  ← no match data yet" if bat == bowl == field == 0.0 else flag
        print(
            f"  {display_name:<28} {bat:>5.1f} {bowl:>6.1f} "
            f"{field:>6.1f} {role_bucket(user):>12}{flag}"
        )

    print("\n" + "=" * 68)
    print("EXACT TEAM SPLIT (3D: bat + bowl + field, plus role/top-player spread)")
    print("=" * 68)

    team_a, team_b = balance_teams_3d(players)
    a_bat, a_bowl, a_field = team_totals(team_a)
    b_bat, b_bowl, b_field = team_totals(team_b)

    print_team("Team A", team_a)
    print_team("Team B", team_b)

    print("\n  Balance check:")
    print(verdict(abs(a_bat - b_bat), "Batting "))
    print(verdict(abs(a_bowl - b_bowl), "Bowling "))
    print(verdict(abs(a_field - b_field), "Fielding"))
    print()


if __name__ == "__main__":
    main()
