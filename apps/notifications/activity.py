"""Activity-feed emit helper + presentation config.

`emit()` is the single entry point signal receivers (and any future caller) use
to drop a row into the club-wide feed. `KIND_STYLE` maps each event kind to its
row icon + colour and the tab it belongs to, mirroring the design's ROW_CFG in
design_handoff/ui_kits/indcric_web/NotificationsScreen.jsx.
"""
import logging

from django.contrib.contenttypes.models import ContentType
from django.db import transaction

from .models import ActivityEvent

logger = logging.getLogger(__name__)

# kind -> row presentation. `tab` is which filter tab the row falls under
# (None = only ever shows under "All"). Colours are Tailwind utility classes;
# `icon` selects the inline SVG in partials/_activity_row.html.
KIND_STYLE = {
    ActivityEvent.KIND_SESSION:  {'bg': 'bg-pitch-50',    'fg': 'text-pitch-700',   'icon': 'calendar', 'tab': 'sessions'},
    ActivityEvent.KIND_RSVP:     {'bg': 'bg-emerald-100', 'fg': 'text-emerald-800', 'icon': 'check',    'tab': 'sessions'},
    ActivityEvent.KIND_PAYMENT:  {'bg': 'bg-amber-50',    'fg': 'text-amber-800',   'icon': 'wallet',   'tab': 'payments'},
    ActivityEvent.KIND_MATCH:    {'bg': 'bg-amber-100',   'fg': 'text-amber-800',   'icon': 'trophy',   'tab': 'match'},
    ActivityEvent.KIND_MENTION:  {'bg': 'bg-sky-100',     'fg': 'text-sky-800',     'icon': 'chat',     'tab': 'mentions'},
    ActivityEvent.KIND_DONATION: {'bg': 'bg-emerald-50',  'fg': 'text-emerald-700', 'icon': 'heart',    'tab': 'donations'},
    ActivityEvent.KIND_TEAM:     {'bg': 'bg-purple-100',  'fg': 'text-purple-800',  'icon': 'users',    'tab': 'sessions'},
    ActivityEvent.KIND_PING:     {'bg': 'bg-stone-100',   'fg': 'text-stone-700',   'icon': 'send',     'tab': None},
}

# An RSVP that's a 'no' vote — same tab as the 'yes' style, but red X.
# Picked in _decorate() by body-text inspection (the signal writes 'is out of'
# for no votes; see signals.on_vote). Kept separate from KIND_STYLE so the
# (kind → style) map stays 1:1 and dedup_key keeps working on vote flips.
RSVP_NO_STYLE = {'bg': 'bg-red-100', 'fg': 'text-red-700', 'icon': 'x', 'tab': 'sessions'}

# Tabs shown on the feed, in order. 'all' is the catch-all. Each maps to the set
# of kinds it includes (derived from KIND_STYLE['tab']). 'Donations' extends the
# design's five tabs since it's the headline event with no home otherwise.
FEED_TABS = [
    ('all', 'All'),
    ('sessions', 'Sessions'),
    ('payments', 'Payments'),
    ('match', 'Match'),
    ('donations', 'Donations'),
    ('mentions', 'Mentions'),
]

# tab key -> kinds it filters to (built once from KIND_STYLE).
TAB_KINDS = {}
for _kind, _style in KIND_STYLE.items():
    if _style['tab']:
        TAB_KINDS.setdefault(_style['tab'], []).append(_kind)


def emit(kind, body, *, actor=None, url='', action_label='', context='', target=None, dedup=False):
    """Create (or, when ``dedup``, refresh) an ActivityEvent.

    With ``dedup=True`` and a ``target``, this update_or_create's on a dedup_key
    of "{kind}:{ct}:{oid}" — so a state-change event (match result, payment
    received) keeps exactly one row per (kind, target), refreshing its body if
    re-emitted (e.g. a re-finalized winner). The partial unique constraint on
    dedup_key makes that race-safe under concurrent saves.

    Prefer :func:`safe_emit` from signal receivers — it wraps this in a savepoint
    so a feed-write failure can't poison the caller's transaction.
    """
    content_type = object_id = None
    if target is not None:
        content_type = ContentType.objects.get_for_model(target.__class__)
        object_id = target.pk

    fields = dict(
        kind=kind, body=body, actor=actor, url=url,
        action_label=action_label, context=context,
        content_type=content_type, object_id=object_id,
    )

    if dedup and content_type is not None:
        dedup_key = f"{kind}:{content_type.id}:{object_id}"
        obj, _ = ActivityEvent.objects.update_or_create(dedup_key=dedup_key, defaults=fields)
        return obj

    return ActivityEvent.objects.create(dedup_key='', **fields)


def safe_emit(*args, **kwargs):
    """emit() inside its own savepoint, with failures logged not raised.

    Signal receivers run synchronously inside the caller's transaction (the bank
    importer and payment-confirm view both save inside ``transaction.atomic()``).
    On Postgres, any DB error escaping a receiver poisons the whole transaction —
    a swallowed exception is NOT enough, the donation/payment save still dies. The
    savepoint contains the failure so only the feed write rolls back."""
    try:
        with transaction.atomic():
            return emit(*args, **kwargs)
    except Exception:
        body = kwargs.get('body') or (args[1] if len(args) > 1 else '?')
        logger.exception("activity feed emit failed: %s", body)
        return None
