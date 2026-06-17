import hashlib
import hmac
import json
import logging
import re
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

from . import bot_messages
from .activity import FEED_TABS, KIND_STYLE, REACTION_EMOJIS, TAB_KINDS
from .models import ActivityEvent, ActivityFeedState, BotEvent, Reaction, seen_at_for


RSVP_PATTERN = re.compile(r'^\s*(yes|no|y|n|✅|❌|1|2)\s*(?:[#\s]*(\d+))?\s*$', re.IGNORECASE)

logger = logging.getLogger(__name__)
User = get_user_model()


def _bad(msg, status=400):
    return JsonResponse({'ok': False, 'error': msg}, status=status)


@csrf_exempt
def whatsapp_webhook(request):
    if request.method == 'GET':
        return _verify_webhook(request)
    if request.method == 'POST':
        return _handle_whatsapp_message(request)
    return HttpResponse(status=405)


def _verify_webhook(request):
    mode = request.GET.get('hub.mode')
    token = request.GET.get('hub.verify_token')
    challenge = request.GET.get('hub.challenge')
    expected = getattr(settings, 'WHATSAPP_VERIFY_TOKEN', '')
    if mode == 'subscribe' and token == expected:
        return HttpResponse(challenge, content_type='text/plain')
    return HttpResponse('Forbidden', status=403)


def _verify_signature(request):
    """Verify Meta's X-Hub-Signature-256 against the raw body using WHATSAPP_APP_SECRET.

    Returns True if signature is valid, or if no secret is configured (dev mode).
    Returns False only when a secret is configured AND the signature is missing/invalid.
    """
    secret = getattr(settings, 'WHATSAPP_APP_SECRET', '')
    if not secret:
        return True  # dev / not configured

    header = request.headers.get('X-Hub-Signature-256', '')
    if not header.startswith('sha256='):
        return False
    expected = hmac.new(
        secret.encode('utf-8'), request.body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(header[len('sha256='):], expected)


def _handle_whatsapp_message(request):
    if not _verify_signature(request):
        logger.warning('WhatsApp webhook signature verification failed')
        return HttpResponse('Forbidden', status=403)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return HttpResponse(status=400)

    try:
        for entry in body.get('entry', []):
            for change in entry.get('changes', []):
                value = change.get('value', {})
                for msg in value.get('messages', []):
                    _process_message(msg, value)
                for status in value.get('statuses', []):
                    _process_status(status)
    except Exception:
        logger.exception('Error processing WhatsApp webhook payload')

    return HttpResponse('OK', status=200)


def _normalize_inbound_phone(raw):
    """Meta sends `from` as E.164 without leading '+' (e.g. '32471123456').
    Stored phones include the '+'. Normalise inbound to match."""
    phone = (raw or '').strip()
    if phone and not phone.startswith('+'):
        phone = '+' + phone
    return phone


def _extract_text(msg):
    """Pull the user's text from text, button, or list-reply payloads.

    Returns the original case-preserved string — callers lowercase as needed.
    The RSVP_PATTERN regex has re.IGNORECASE so it doesn't care, but we want
    the original text available for echoing back in 'didn't understand' replies.
    """
    msg_type = msg.get('type')
    if msg_type == 'text':
        return (msg.get('text', {}).get('body', '') or '').strip()
    if msg_type == 'interactive':
        interactive = msg.get('interactive', {})
        sub = interactive.get('type')
        if sub == 'button_reply':
            br = interactive.get('button_reply', {})
            return (br.get('id') or br.get('title') or '').strip()
        if sub == 'list_reply':
            lr = interactive.get('list_reply', {})
            return (lr.get('id') or lr.get('title') or '').strip()
    if msg_type == 'button':
        return (msg.get('button', {}).get('text', '') or '').strip()
    return ''


def _process_status(status):
    """Log a Meta delivery-status callback (sent / delivered / read / failed).

    Meta can send multiple status updates for one outbound message — `sent`,
    then `delivered`, then `read`, or a terminal `failed` with an `errors` list.
    We key BotEvent rows by `{wamid}:{state}` so each transition is its own row
    and duplicate webhook deliveries hit the unique constraint cleanly.

    The failure case is the one that matters for diagnosis: `errors[0].code` /
    `errors[0].title` tell us *why* delivery didn't reach the recipient (e.g.
    131026 = receiver unreachable, 131047 = re-engagement required, 131056 =
    pair rate limit, 470 = template paused).
    """
    wamid = status.get('id', '')
    state = (status.get('status') or '').lower()
    recipient_raw = status.get('recipient_id', '')
    if not wamid or not state:
        return

    recipient = _normalize_inbound_phone(recipient_raw)
    errors = status.get('errors') or []
    error_code = errors[0].get('code') if errors else None
    error_title = errors[0].get('title') if errors else None

    if state == 'failed':
        logger.error(
            'WhatsApp delivery failed to %s (wamid=%s): code=%s — %s',
            recipient, wamid, error_code, error_title,
        )
    else:
        logger.info('WhatsApp status %s for %s (wamid=%s)', state, recipient, wamid)

    user = None
    if recipient:
        user = User.objects.filter(phone=recipient).first()

    try:
        BotEvent.objects.create(
            wa_message_id=f"{wamid}:{state}",
            phone=recipient,
            user=user,
            action='wa_status',
            direction=BotEvent.OUTBOUND,
            payload={
                'wamid': wamid,
                'status': state,
                'recipient_id': recipient_raw,
                'timestamp': status.get('timestamp'),
                'errors': errors,
                'conversation': status.get('conversation'),
                'pricing': status.get('pricing'),
            },
        )
    except IntegrityError:
        pass  # duplicate webhook delivery — Meta retries on non-2xx


def _process_message(msg, value):
    wa_message_id = msg.get('id', '')
    phone = _normalize_inbound_phone(msg.get('from', ''))
    text = _extract_text(msg)

    if not text:
        return

    rsvp = RSVP_PATTERN.match(text)
    if rsvp:
        token = rsvp.group(1).lower()
        session_id = int(rsvp.group(2)) if rsvp.group(2) else None
        choice = 'yes' if token in ('yes', 'y', '✅', '1') else 'no'
        _handle_rsvp(wa_message_id, phone, choice, msg, session_id=session_id)
        return

    text_lower = text.lower()
    if text_lower in ('balance', 'bal', '/balance', 'wallet'):
        _handle_balance(wa_message_id, phone, msg)
    elif text_lower in ('status', 'poll', 'who', 'count', '/status'):
        _handle_status(wa_message_id, phone, msg)
    elif text_lower in ('score', 'scores', '/score', 'live'):
        _handle_score(wa_message_id, phone, msg)
    elif text_lower in ('history', 'hist', '/history', 'games'):
        _handle_history(wa_message_id, phone, msg)
    elif text_lower in ('help', '/help', '?'):
        _handle_help(wa_message_id, phone, msg)
    else:
        logger.info('Unrecognised WhatsApp message from %s: %s', phone, text)
        _handle_unknown(wa_message_id, phone, text, msg)


def _handle_rsvp(wa_message_id, phone, choice, raw, session_id=None):
    """Record an inbound RSVP and reply with a confirmation.

    If session_id is given (from a wa.me deep link), target that specific
    session's poll; otherwise fall back to the latest open poll. Replies are
    sent inside the user's free 24h service window (the same inbound that
    triggered this handler opened it), so they don't cost anything.
    """
    from apps.polls.models import Poll, Vote
    from .services import send_text_message

    user = User.objects.filter(phone=phone).first()

    payload = {'raw': raw, 'requested_session_id': session_id, 'choice': choice}
    if not _log_inbound(wa_message_id, phone, user, 'rsvp', payload):
        return  # duplicate webhook delivery — first call already handled this

    if user is None:
        logger.warning('WhatsApp RSVP from unknown phone %s', phone)
        send_text_message(phone, bot_messages.not_recognised())
        return

    poll_obj = None
    if session_id is not None:
        poll_obj = Poll.objects.filter(session_id=session_id, is_open=True).first()
        if poll_obj is None:
            logger.info(
                'RSVP from %s targeted session %s but no open poll for it',
                phone, session_id,
            )

    if poll_obj is None:
        poll_obj = _next_open_poll()
    if poll_obj is None:
        send_text_message(phone, bot_messages.no_active_poll())
        return

    Vote.objects.update_or_create(
        poll=poll_obj, user=user, defaults={'choice': choice}
    )

    session = poll_obj.session
    date_str = session.date.strftime("%a %d %b")
    yes_names, no_names = _poll_voter_names(poll_obj)
    send_text_message(
        phone,
        bot_messages.rsvp_recorded(choice, session.name, date_str, yes_names, no_names),
    )


def _log_inbound(wa_message_id, phone, user, action, payload):
    try:
        BotEvent.objects.create(
            wa_message_id=wa_message_id, phone=phone, user=user,
            action=action, direction=BotEvent.INBOUND, payload=payload,
        )
        return True
    except IntegrityError:
        return False


def _handle_balance(wa_message_id, phone, raw):
    from django.db.models import Sum
    from apps.payments.models import Wallet, Payment
    from .services import send_text_message

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        if _log_inbound(wa_message_id, phone, None, 'balance', raw):
            send_text_message(phone, bot_messages.not_recognised())
        return

    if not _log_inbound(wa_message_id, phone, user, 'balance', raw):
        return  # duplicate webhook

    wallet_total = Wallet.objects.filter(user=user).aggregate(s=Sum('amount'))['s'] or 0
    unpaid = (
        Payment.objects.filter(user=user, status='pending')
        .select_related('session')
        .order_by('session__date')
    )
    unpaid_rows = [(p.session.name, p.amount) for p in unpaid]
    send_text_message(phone, bot_messages.balance(wallet_total, unpaid_rows))


def _handle_history(wa_message_id, phone, raw):
    """Reply with the user's last few games — their batting/bowling line, result,
    and per-session cost — plus a career summary and wallet balance. Read-only.

    Stats derive from the ball-by-ball ledger (apps.matches.scoring). Cost is
    session.cost_per_person and paid is SessionPlayer.paid (the Payment table
    isn't populated in this deployment)."""
    from django.db.models import Sum
    from apps.payments.models import Wallet
    from apps.sessions.models import SessionPlayer
    from apps.matches.scoring import career_stats, player_recent_matches
    from .services import send_text_message

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        if _log_inbound(wa_message_id, phone, None, 'history', raw):
            send_text_message(phone, bot_messages.not_recognised())
        return

    if not _log_inbound(wa_message_id, phone, user, 'history', raw):
        return  # duplicate webhook

    paid_by_session = dict(
        SessionPlayer.objects.filter(user=user).values_list('session_id', 'paid')
    )
    games = []
    for g in player_recent_matches(user, limit=6):
        s = g['session']
        games.append({
            'session': s.name if s else g['match'].name,
            'match': g['match'].name,
            'date': s.date.strftime("%a %d %b") if s and s.date else '',
            'runs': g['runs'], 'balls': g['balls'], 'wickets': g['wickets'],
            'won': g['won'],
            'amount': s.cost_per_person if s else None,
            'paid': paid_by_session.get(s.id) if s else None,
        })
    wallet_total = Wallet.objects.filter(user=user).aggregate(s=Sum('amount'))['s'] or 0
    send_text_message(phone, bot_messages.history(games, career_stats(user), wallet_total))


def _display_name(user):
    """Human-readable name for use in bot replies. Prefers first name, falls
    back to username so we never show a blank entry in the voter lists."""
    return (user.first_name or user.username or '').strip() or '(unknown)'


def _poll_voter_names(poll):
    """(yes_names, no_names) display-name lists for a poll, name-sorted."""
    def names(choice):
        return [
            _display_name(v.user)
            for v in poll.votes.filter(choice=choice)
            .select_related('user')
            .order_by('user__first_name', 'user__username')
        ]
    return names('yes'), names('no')


def _handle_status(wa_message_id, phone, raw):
    """Reply with the current open poll's vote counts and voter lists."""
    from apps.polls.models import Poll
    from .services import send_text_message

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        if _log_inbound(wa_message_id, phone, None, 'status', raw):
            send_text_message(phone, bot_messages.not_recognised())
        return

    if not _log_inbound(wa_message_id, phone, user, 'status', raw):
        return

    poll = _next_open_poll()
    if poll is None:
        send_text_message(phone, bot_messages.no_active_poll())
        return

    session = poll.session
    date_str = session.date.strftime("%a %d %b")
    yes_names, no_names = _poll_voter_names(poll)
    send_text_message(phone, bot_messages.status(
        session.name, date_str, yes_names, no_names,
    ))


def _next_open_poll():
    """Pick the *next upcoming* open poll (closest future date+time first),
    falling back to the most recent past open poll if nothing's upcoming."""
    from apps.polls.models import Poll
    today = timezone.localdate()
    upcoming = (
        Poll.objects
        .filter(is_open=True, session__date__gte=today)
        .order_by('session__date', 'session__time')
        .select_related('session')
        .first()
    )
    if upcoming is not None:
        return upcoming
    return (
        Poll.objects
        .filter(is_open=True)
        .order_by('-session__date', '-session__time')
        .select_related('session')
        .first()
    )


def _handle_score(wa_message_id, phone, raw):
    """Reply with live scores for the most relevant session.

    Picks today's session if there is one, else the most recent past session,
    else the next upcoming one. For each match in that session:
      - no innings yet → 'not started'
      - innings exist → totals derived from the Delivery ledger via scoring.innings_score
    """
    from apps.sessions.models import Session
    from apps.matches.scoring import innings_score
    from .services import send_text_message

    user = User.objects.filter(phone=phone).first()
    if user is None:
        if _log_inbound(wa_message_id, phone, None, 'score', raw):
            send_text_message(phone, bot_messages.not_recognised())
        return

    if not _log_inbound(wa_message_id, phone, user, 'score', raw):
        return

    today = timezone.localdate()
    session = (
        Session.objects
        .filter(date__lte=today)
        .order_by('-date', '-time')
        .first()
    )
    if session is None:
        session = (
            Session.objects
            .filter(date__gte=today)
            .order_by('date', 'time')
            .first()
        )
    if session is None:
        send_text_message(phone, bot_messages.no_recent_session())
        return

    matches = list(
        session.matches
        .prefetch_related('innings__batting_team', 'teams')
        .order_by('id')
    )

    if not matches:
        date_str = session.date.strftime("%a %d %b")
        send_text_message(phone, bot_messages.match_not_started(session.name, date_str))
        return

    match_blocks = []
    for m in matches:
        innings_lines = []
        for inn in m.innings.order_by('number'):
            s = innings_score(inn)
            innings_lines.append(
                f"{inn.batting_team.name}: {s['runs']}/{s['wickets']} ({s['overs']})"
            )
        match_blocks.append({
            'name': m.name,
            'innings': innings_lines,
            'winner': m.winner.name if m.winner_id else None,
        })

    date_str = session.date.strftime("%a %d %b")
    send_text_message(phone, bot_messages.score(session.name, date_str, match_blocks))


def _handle_help(wa_message_id, phone, raw):
    from .services import send_text_message

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        user = None

    if not _log_inbound(wa_message_id, phone, user, 'help', raw):
        return
    send_text_message(phone, bot_messages.help_text())


def _handle_unknown(wa_message_id, phone, text, raw):
    """Reply when we couldn't parse the message. Echoes the user's input back
    (with the case they actually typed) so they can see what got through —
    helpful when mobile auto-capitalize or autocorrect mangled their RSVP.
    """
    from .services import send_text_message

    user = User.objects.filter(phone=phone).first()
    if not _log_inbound(wa_message_id, phone, user, 'unknown', {'raw': raw, 'text': text}):
        return

    safe_echo = text[:60] if text else ''
    send_text_message(phone, bot_messages.unknown(safe_echo))


def run_reminders_view(request):
    """Hit by an external scheduler (cron-job.org / GitHub Actions) every ~15 min.

    Auth via ?token=$BOT_WEBHOOK_TOKEN query string. Doubles as a Render keepalive.
    """
    expected = getattr(settings, 'BOT_WEBHOOK_TOKEN', '')
    token = request.GET.get('token', '')
    if not expected or token != expected:
        return _bad('unauthorized', 401)

    from .services import send_session_reminders
    counts = send_session_reminders()
    return JsonResponse({'ok': True, 'sent': counts})


# ─────────────────────────── Activity feed (in-app) ───────────────────────────

_DEFAULT_STYLE = KIND_STYLE[ActivityEvent.KIND_PING]


def _reaction_summary(event, user):
    """For each palette emoji: its count on this event and whether the viewer
    has reacted with it. Reads from event.reactions (prefetch on the list)."""
    counts = {}
    mine = set()
    for r in event.reactions.all():
        counts[r.emoji] = counts.get(r.emoji, 0) + 1
        if r.user_id == user.id:
            mine.add(r.emoji)
    return [
        {'emoji': e, 'count': counts.get(e, 0), 'reacted': e in mine}
        for e in REACTION_EMOJIS
    ]


def _decorate(events, user, seen_before):
    """Attach row presentation + read-state + reaction summary to each event for
    the template. Own actions never show as unread (mirrors the bell count)."""
    for ev in events:
        ev.style = KIND_STYLE.get(ev.kind, _DEFAULT_STYLE)
        ev.is_unread = ev.created_at > seen_before and ev.actor_id != user.id
        ev.reactions_view = _reaction_summary(ev, user)
    return events


def _feed_events(user, tab, seen_before, limit=100):
    # No select_related('actor'): the row template never renders the actor, and
    # is_unread reads the actor_id FK column already on the row.
    qs = ActivityEvent.objects.prefetch_related('reactions')
    if tab != 'all' and tab in TAB_KINDS:
        qs = qs.filter(kind__in=TAB_KINDS[tab])
    events = list(qs[:limit])
    return _decorate(events, user, seen_before)


@login_required
def activity_feed_view(request):
    """The club-wide activity feed (the design's Notifications/Activity screen).
    Tabs filter by kind via HTMX (list partial swap). Read-state is explicit —
    opening the feed does NOT auto-clear; the 'Mark all read' button does."""
    tab = request.GET.get('tab', 'all')
    seen_before = seen_at_for(request.user)
    events = _feed_events(request.user, tab, seen_before)
    context = {
        'events': events,
        'tab': tab,
        'tabs': FEED_TABS,
    }
    if request.htmx:
        return render(request, 'notifications/partials/_activity_list.html', context)
    return render(request, 'notifications/pages/activity.html', context)


@login_required
@require_POST
def activity_react_view(request, activity_id):
    """Toggle the viewer's reaction with `emoji` on one event; re-render that
    row's reaction bar for the HTMX swap."""
    event = get_object_or_404(ActivityEvent, pk=activity_id)
    emoji = request.POST.get('emoji', '')
    if emoji in REACTION_EMOJIS:
        existing = Reaction.objects.filter(
            activity=event, user=request.user, emoji=emoji
        ).first()
        if existing:
            existing.delete()
        else:
            # get_or_create guards the unique constraint against a double-tap race.
            Reaction.objects.get_or_create(activity=event, user=request.user, emoji=emoji)
    event.reactions_view = _reaction_summary(event, request.user)
    return render(request, 'notifications/partials/_reaction_bar.html', {'event': event})


@login_required
@require_POST
def activity_read_all_view(request):
    """Mark everything read (set last_seen = now). Re-renders the list with the
    unread dots cleared and OOB-swaps the header bell badge to zero."""
    state, _ = ActivityFeedState.objects.get_or_create(user=request.user)
    state.last_seen_at = timezone.now()
    state.save(update_fields=['last_seen_at'])

    # tab arrives in the POST body (hx-include of the hidden tab field).
    tab = request.POST.get('tab') or request.GET.get('tab') or 'all'
    events = _feed_events(request.user, tab, state.last_seen_at)
    return render(request, 'notifications/partials/_read_all_response.html', {
        'events': events,
        'tab': tab,
        'activity_unread': 0,
    })
