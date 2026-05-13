---
name: team-management
description: Use when working on Team assignment, smart team balancing, Match scoring, or PlayerProfile stats in the IndCric Django app. Covers the Session → Match → Team → Player chain, SessionPlayer team field, skill-rating-based auto-split algorithm, save_teams_view HTMX flow, and rating validation (0-5 Decimal). Trigger on edits to Match/Team/Player/SessionPlayer models, team assignment views/templates, or any work involving `batting_rating`/`bowling_rating`/`fielding_rating`.
---

# Team Management & Scoring

Use this skill when working on team assignment, smart player splitting, match scoring, or player stats.

## Context

Each `Session` can have one `Match`. A `Match` has two or more `Team` objects. Players are assigned to teams via `SessionPlayer.team`. The goal is to have balanced teams based on player skill ratings.

## Key Models

```python
# Session → Match → Team → Player chain
Match.session    → Session (FK, nullable)
Match.winner     → Team (FK, nullable)

Team.match       → Match
Team.name        = str
Team.captain     → User

Player.user      → User
Player.team      → Team
Player.role      = str
Player.paid      = bool

# SessionPlayer is the authoritative player-in-session record
SessionPlayer.session  → Session
SessionPlayer.user     → User
SessionPlayer.team     → Team (assigned team)
SessionPlayer.paid     = bool
```

## Smart Team Splitting Algorithm

When auto-balancing teams by skill, split players across two teams so total ratings are as equal as possible.

```python
def balance_teams(players):
    """
    players: list of User objects with batting_rating + bowling_rating
    Returns: (team_a_players, team_b_players)
    """
    # Score = avg(batting_rating, bowling_rating) or by primary role
    def score(user):
        if user.role == 'batsman':
            return float(user.batting_rating or 0)
        elif user.role == 'bowler':
            return float(user.bowling_rating or 0)
        else:  # allrounder
            return float((user.batting_rating + user.bowling_rating) / 2)

    ranked = sorted(players, key=score, reverse=True)
    team_a, team_b = [], []
    score_a = score_b = 0

    for player in ranked:
        if score_a <= score_b:
            team_a.append(player)
            score_a += score(player)
        else:
            team_b.append(player)
            score_b += score(player)

    return team_a, team_b
```

Alternatively split by role: alternate assigning top batsmen and bowlers to each team.

## Save Teams View Pattern

The `save_teams_view` in views.py:
1. Receives POST with `team_a_players[]` and `team_b_players[]` user ID lists
2. Gets or creates Match for the session
3. Deletes existing teams and re-creates Team A + Team B
4. Creates/updates SessionPlayer assignments
5. Returns HTMX partial if `request.htmx`

## Scoring (to implement)

### Match-level scores
Add to `Team` model:
```python
runs_scored = models.IntegerField(default=0)
wickets_lost = models.IntegerField(default=0)
overs_played = models.DecimalField(max_digits=4, decimal_places=1, default=0)
```

### Individual stats per session
Add to `SessionPlayer` or a new `PlayerMatchStats` model:
```python
class PlayerMatchStats(models.Model):
    session_player = models.OneToOneField(SessionPlayer, on_delete=models.CASCADE)
    runs = models.IntegerField(default=0)
    balls_faced = models.IntegerField(default=0)
    wickets = models.IntegerField(default=0)
    overs_bowled = models.DecimalField(max_digits=4, decimal_places=1, default=0)
    catches = models.IntegerField(default=0)
```

Aggregate into `PlayerProfile` after each session.

## Player Skill Ratings

Ratings are on User model: `batting_rating`, `bowling_rating`, `fielding_rating` (Decimal 0–5).

- **Admin edit**: `manage_users` page → edit user form (staff only)
- **Self edit**: `profile_edit_view` using `ProfileForm`

Always validate ratings are in range [0, 5] in the form:
```python
def clean_batting_rating(self):
    val = self.cleaned_data['batting_rating']
    if not (0 <= val <= 5):
        raise forms.ValidationError("Rating must be between 0 and 5.")
    return val
```

## Team Display in Session Detail

The `session_detail.html` template shows two columns (Team A / Team B). Each player chip shows:
- Name
- Role icon (bat.png / ball.png)
- Rating badge

Use Alpine.js `x-data` to handle drag-and-drop or click-to-assign team swaps client-side, then POST to `save-teams/`.

## Testing Checklist
- [ ] Auto-balance produces teams with roughly equal total ratings
- [ ] Manual team reassignment persists correctly
- [ ] Match winner can be set and is displayed on session page
- [ ] Player stats aggregate to PlayerProfile correctly
- [ ] Skill ratings cannot be set outside 0–5 range
- [ ] Team names are editable inline (existing HTMX feature)
