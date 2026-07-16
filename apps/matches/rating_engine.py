"""Player rating engine derived from completed scored matches."""

from decimal import Decimal, ROUND_HALF_UP

from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Count, F, Q

from .models import Delivery, Match, Player, PlayerMatchStat


DEFAULT_RATING = Decimal('2.5')


def completed_matches_queryset():
    """Matches with at least two innings and every innings closed."""
    return (
        Match.objects
        .annotate(
            innings_count=Count('innings', distinct=True),
            closed_innings_count=Count(
                'innings',
                filter=Q(innings__is_closed=True),
                distinct=True,
            ),
        )
        .filter(innings_count__gte=2, innings_count=F('closed_innings_count'))
        .order_by('session__date', 'id')
    )


def _is_completed_match(match):
    innings = list(match.innings.all())
    return len(innings) >= 2 and all(innings_row.is_closed for innings_row in innings)


def _empty_stat(user):
    return {
        'user': user,
        'runs': 0,
        'balls_faced': 0,
        'wickets': 0,
        'balls_bowled': 0,
        'runs_conceded': 0,
        'catches': 0,
        'runouts': 0,
        'stumpings': 0,
    }


def _collect_match_stats(match):
    stats = {}

    def slot(player):
        user = player.user
        if user.id not in stats:
            stats[user.id] = _empty_stat(user)
        return stats[user.id]

    for player in Player.objects.filter(team__match=match).select_related('user'):
        slot(player)

    deliveries = (
        Delivery.objects
        .filter(innings__match=match)
        .select_related('striker__user', 'bowler__user', 'fielder__user')
        .order_by('innings__number', 'sequence')
    )
    for delivery in deliveries:
        batter = slot(delivery.striker)
        batter['runs'] += delivery.runs_off_bat
        if delivery.extra_type != Delivery.EXTRA_WIDE:
            batter['balls_faced'] += 1

        bowler = slot(delivery.bowler)
        if delivery.is_legal:
            bowler['balls_bowled'] += 1
        bowler['runs_conceded'] += delivery.runs_conceded
        if delivery.is_wicket and delivery.dismissal_type in Delivery.BOWLER_DISMISSALS:
            bowler['wickets'] += 1

        if delivery.is_wicket and delivery.fielder_id:
            fielder = slot(delivery.fielder)
            if delivery.dismissal_type == 'caught':
                fielder['catches'] += 1
            elif delivery.dismissal_type == 'runout':
                fielder['runouts'] += 1
            elif delivery.dismissal_type == 'stumped':
                fielder['stumpings'] += 1

    return stats


def _upsert_match_stats(match, stats_by_user_id):
    for stat in stats_by_user_id.values():
        PlayerMatchStat.objects.update_or_create(
            match=match,
            user=stat['user'],
            defaults={
                'session': match.session,
                'runs': stat['runs'],
                'balls_faced': stat['balls_faced'],
                'wickets': stat['wickets'],
                'balls_bowled': stat['balls_bowled'],
                'runs_conceded': stat['runs_conceded'],
                'catches': stat['catches'],
                'runouts': stat['runouts'],
                'stumpings': stat['stumpings'],
            },
        )


def _clamp(value, low=0.0, high=5.0):
    return max(low, min(high, value))


def _batting_raw(stat):
    if stat.balls_faced == 0:
        return None
    strike_rate = (stat.runs / stat.balls_faced) * 100
    return _clamp(strike_rate / 30.0)


def _bowling_raw(stat):
    if stat.balls_bowled == 0:
        return None
    economy = (stat.runs_conceded / stat.balls_bowled) * 6
    wickets_points = min(stat.wickets * 1.0, 5.0)
    economy_points = _clamp((12 - economy) / 2, 0.0, 2.5)
    return _clamp(wickets_points + economy_points)


def _fielding_raw(stat):
    dismissals = stat.catches + stat.runouts + stat.stumpings
    return _clamp(dismissals * 1.25)


def _weighted_average(values_newest_first):
    valid = [value for value in values_newest_first if value is not None]
    if not valid:
        return None
    total_weight = 0
    weighted_sum = 0.0
    count = len(valid)
    for index, value in enumerate(valid):
        weight = count - index
        weighted_sum += weight * value
        total_weight += weight
    return weighted_sum / total_weight


def _to_rating_decimal(value):
    if value is None:
        return Decimal('0.0')
    return Decimal(str(_clamp(value))).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)


def _reset_to_default(user):
    user.batting_rating = DEFAULT_RATING
    user.bowling_rating = DEFAULT_RATING
    user.fielding_rating = DEFAULT_RATING
    user.save(update_fields=['batting_rating', 'bowling_rating', 'fielding_rating'])


def recalculate_user_ratings(user, reset_if_empty=False):
    stat_rows = list(
        PlayerMatchStat.objects
        .filter(user=user)
        .select_related('session', 'match')
        .order_by('-session__date', '-session__id', '-match_id')
    )
    if not stat_rows:
        if reset_if_empty:
            _reset_to_default(user)
        return False

    batting_avg = _weighted_average([_batting_raw(stat) for stat in stat_rows])
    bowling_avg = _weighted_average([_bowling_raw(stat) for stat in stat_rows])
    fielding_avg = _weighted_average([_fielding_raw(stat) for stat in stat_rows])

    user.batting_rating = _to_rating_decimal(batting_avg)
    user.bowling_rating = _to_rating_decimal(bowling_avg)
    user.fielding_rating = _to_rating_decimal(fielding_avg)
    user.save(update_fields=['batting_rating', 'bowling_rating', 'fielding_rating'])
    return True


@transaction.atomic
def compute_match_ratings(match):
    """Create/update match stat rows and recalculate ratings for participants."""
    if not _is_completed_match(match):
        return 0

    stats_by_user_id = _collect_match_stats(match)
    if not stats_by_user_id:
        return 0

    _upsert_match_stats(match, stats_by_user_id)

    for stat in stats_by_user_id.values():
        recalculate_user_ratings(stat['user'], reset_if_empty=True)

    return len(stats_by_user_id)


@transaction.atomic
def clear_match_ratings(match):
    """Remove stat rows for a match that is no longer completed."""
    user_ids = list(
        PlayerMatchStat.objects
        .filter(match=match)
        .values_list('user_id', flat=True)
        .distinct()
    )
    PlayerMatchStat.objects.filter(match=match).delete()
    User = get_user_model()
    for user in User.objects.filter(id__in=user_ids):
        recalculate_user_ratings(user, reset_if_empty=True)
    return len(user_ids)


@transaction.atomic
def rebuild_all_ratings():
    """Rebuild all stat rows and user ratings from completed matches."""
    User = get_user_model()
    PlayerMatchStat.objects.all().delete()

    affected_user_ids = set()
    processed_matches = 0
    for match in completed_matches_queryset().prefetch_related('innings'):
        stats_by_user_id = _collect_match_stats(match)
        if not stats_by_user_id:
            continue
        _upsert_match_stats(match, stats_by_user_id)
        affected_user_ids.update(stats_by_user_id.keys())
        processed_matches += 1

    for user in User.objects.filter(id__in=affected_user_ids):
        recalculate_user_ratings(user, reset_if_empty=True)

    User.objects.exclude(id__in=affected_user_ids).update(
        batting_rating=DEFAULT_RATING,
        bowling_rating=DEFAULT_RATING,
        fielding_rating=DEFAULT_RATING,
    )

    return processed_matches, len(affected_user_ids)
