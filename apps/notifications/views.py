import hashlib
import hmac
import json
import logging
import re
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.contrib.auth import get_user_model

from . import bot_messages
from .activity import FEED_TABS, KIND_STYLE, RSVP_NO_STYLE, TAB_KINDS
from .models import ActivityEvent, ActivityFeedState, BotEvent, seen_at_for


RSVP_PATTERN = re.compile(
    r'^\s*(yes|no|y|n|sat|saturday|sun|sunday|both|all|✅|❌|1|2|3)\s*(?:[#\s]*(\d+))?\s*$',
    re.IGNORECASE,
)

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


def _dm_sink(phone):
    """Default reply sink — a Cloud-API DM back to `phone` (the Meta path).

    Built lazily so the `services.send_text_message` patch target used in tests
    still applies, and so importing this module doesn't pull in `services`."""
    def _send(text):
        from .services import send_text_message
        return send_text_message(phone, text)
    return _send


def dispatch_inbound(wa_message_id, phone, text, chat='dm', reply=None, raw=None,
                     allow_text_rsvp=True, reply_unknown=True, lid='', wa_name=''):
    """Shared inbound parser + dispatcher for BOTH the Meta Cloud-API webhook
    and the group-resident bot's /api/bot/inbound/ endpoint.

    `reply(text)` is the reply sink: a Cloud-API DM for ``chat='dm'`` (default),
    or a group-queue enqueue for ``chat='community'``. `raw` is the source
    payload stored verbatim in the BotEvent audit row. Returns a small result
    dict describing what happened so the group endpoint can translate an RSVP
    into an emoji reaction (✅/❌) instead of a text post.

    `allow_text_rsvp`: when False, typed vote text is NOT counted as a vote.
    Used for GROUP text — members say "yes"/"no" in normal conversation, so free
    text must not record RSVPs. Group votes come ONLY from native poll votes and
    reactions on the bot's own message (the endpoint forwards those as a vote
    with allow_text_rsvp=True). DMs to the bot keep text RSVP (the deep link
    sends 'YES <session_id>').
    `reply_unknown`: when False, an unrecognised message is ignored silently — so
    the bot doesn't reply to every non-command line typed in the group.
    """
    if reply is None:
        reply = _dm_sink(phone)
    if raw is None:
        raw = {}

    if not text:
        return {'kind': 'empty'}

    if allow_text_rsvp:
        rsvp = RSVP_PATTERN.match(text)
        if rsvp:
            token = rsvp.group(1).lower()
            session_id = int(rsvp.group(2)) if rsvp.group(2) else None
            if token in ('yes', 'y', '✅', '1', 'sat', 'saturday'):
                choice = 'yes'
            elif token in ('no', 'n', '❌', '2', 'sun', 'sunday'):
                choice = 'no'
            else:
                choice = 'all'
            result = _handle_rsvp(
                wa_message_id, phone, choice, raw,
                session_id=session_id, reply=reply, chat=chat,
                lid=lid, wa_name=wa_name,
            )
            return {'kind': 'rsvp', **(result or {})}

    text_lower = text.lower()
    if text_lower in ('balance', 'bal', '/balance', 'wallet'):
        _handle_balance(wa_message_id, phone, raw, reply=reply)
        return {'kind': 'command', 'command': 'balance'}
    elif text_lower in ('status', 'poll', 'who', 'count', '/status'):
        _handle_status(wa_message_id, phone, raw, reply=reply)
        return {'kind': 'command', 'command': 'status'}
    elif text_lower in ('score', 'scores', '/score', 'live'):
        _handle_score(wa_message_id, phone, raw, reply=reply)
        return {'kind': 'command', 'command': 'score'}
    elif text_lower in ('history', 'hist', '/history', 'games'):
        _handle_history(wa_message_id, phone, raw, reply=reply)
        return {'kind': 'command', 'command': 'history'}
    elif text_lower in ('help', '/help', '?'):
        _handle_help(wa_message_id, phone, raw, reply=reply)
        return {'kind': 'command', 'command': 'help'}
    else:
        if reply_unknown:
            logger.info('Unrecognised WhatsApp message from %s: %s', phone, text)
            _handle_unknown(wa_message_id, phone, text, raw, reply=reply)
            return {'kind': 'unknown'}
        logger.info('Ignored group message from %s: %s', phone, text)
        return {'kind': 'ignored'}


def _process_message(msg, value):
    """Adapter: turn a Meta-webhook message dict into a dispatch_inbound call.

    Behaviour-preserving wrapper around the shared dispatcher — the Meta path is
    always a DM, so the reply sink defaults to send_text_message and `raw` is the
    original Meta message dict (kept in BotEvent.payload as before)."""
    wa_message_id = msg.get('id', '')
    phone = _normalize_inbound_phone(msg.get('from', ''))
    text = _extract_text(msg)
    dispatch_inbound(wa_message_id, phone, text, chat='dm', raw=msg)


def _handle_rsvp(wa_message_id, phone, choice, raw, session_id=None, reply=None,
                 chat='dm', lid='', wa_name=''):
    """Record an inbound RSVP. Confirms via the reply sink on the DM path; on the
    group path stays silent here (the /api/bot/inbound/ endpoint reacts ✅/❌ to
    the member's message — per-vote text would flood the group).

    Identity: match on phone (DM / wa.me path) first, then on `lid` (group path —
    Community/privacy groups expose only a WhatsApp LID, never the number). An
    unknown LID is logged WITH the member's `wa_name` so an admin can map it to a
    user (set User.wa_lid). Returns {'recorded': bool, 'choice': str, 'reason'?}.
    """
    from apps.polls.models import Poll, Vote
    if reply is None:
        reply = _dm_sink(phone)

    # Identity match, in order of confidence:
    #   1. phone        — DM / wa.me path, or a group that exposes @c.us numbers
    #   2. wa_lid       — already-learned LID for this group member
    #   3. wa_name      — the WhatsApp display name (from the roster), used the
    #                     first time a member votes; we then LEARN their wa_lid.
    user = User.objects.filter(phone=phone).first()
    if user is None and lid:
        user = User.objects.filter(wa_lid=lid).first()
    if user is None and wa_name:
        named = list(User.objects.filter(wa_name__iexact=wa_name)[:2])
        if len(named) == 1:                      # unique name → confident match
            user = named[0]

    # Learn the LID for next time, so future votes match directly (tier 2).
    if user is not None and lid and user.wa_lid != lid:
        User.objects.filter(pk=user.pk).update(wa_lid=lid)

    payload = {'raw': raw, 'requested_session_id': session_id, 'choice': choice,
               'lid': lid, 'wa_name': wa_name}
    if not _log_inbound(wa_message_id, phone, user, 'rsvp', payload):
        return {'recorded': False, 'reason': 'duplicate', 'choice': choice}

    if user is None:
        logger.warning('WhatsApp RSVP from unknown identity phone=%s lid=%s name=%r',
                       phone, lid, wa_name)
        reply(bot_messages.not_recognised())
        return {'recorded': False, 'reason': 'unknown_identity', 'choice': choice}

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
        reply(bot_messages.no_active_poll())
        return {'recorded': False, 'reason': 'no_poll', 'choice': choice}

    session = poll_obj.session
    if choice == 'all' and not session.has_two_date_options:
        reply(bot_messages.invalid_availability_choice(is_two_day=False))
        return {'recorded': False, 'reason': 'invalid_choice', 'choice': choice}

    Vote.objects.update_or_create(
        poll=poll_obj, user=user, defaults={'choice': choice}
    )

    if chat != 'community':
        date_str = session.date.strftime("%a %d %b")
        yes_names, no_names, both_names = _poll_voter_names(poll_obj)
        reply(bot_messages.rsvp_recorded(
            choice, session.name, date_str, yes_names, no_names, both_names,
            is_two_day=session.has_two_date_options,
        ))

    return {'recorded': True, 'choice': choice, 'is_two_day': session.has_two_date_options}


def _log_inbound(wa_message_id, phone, user, action, payload):
    # Savepoint so a duplicate (caught IntegrityError) only rolls back this INSERT
    # — without it, Postgres aborts the whole surrounding transaction and the next
    # query raises TransactionManagementError (matters under ATOMIC_REQUESTS / in
    # the group inbound endpoint where we keep working after a dedupe).
    try:
        with transaction.atomic():
            BotEvent.objects.create(
                wa_message_id=wa_message_id, phone=phone, user=user,
                action=action, direction=BotEvent.INBOUND, payload=payload,
            )
        return True
    except IntegrityError:
        return False


def _handle_balance(wa_message_id, phone, raw, reply=None):
    from django.db.models import Sum
    from apps.payments.models import Wallet, Payment
    if reply is None:
        reply = _dm_sink(phone)

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        if _log_inbound(wa_message_id, phone, None, 'balance', raw):
            reply(bot_messages.not_recognised())
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
    reply(bot_messages.balance(wallet_total, unpaid_rows))


def _handle_history(wa_message_id, phone, raw, reply=None):
    """Reply with the user's last few games — their batting/bowling line, result,
    and per-session cost — plus a career summary and wallet balance. Read-only.

    Stats derive from the ball-by-ball ledger (apps.matches.scoring). Cost is
    session.cost_per_person and paid is SessionPlayer.paid (the Payment table
    isn't populated in this deployment)."""
    from django.db.models import Sum
    from apps.payments.models import Wallet
    from apps.sessions.models import SessionPlayer
    from apps.matches.scoring import career_stats, player_recent_matches
    if reply is None:
        reply = _dm_sink(phone)

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        if _log_inbound(wa_message_id, phone, None, 'history', raw):
            reply(bot_messages.not_recognised())
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
    reply(bot_messages.history(games, career_stats(user), wallet_total))


def _display_name(user):
    """Human-readable name for use in bot replies. Prefers first name, falls
    back to username so we never show a blank entry in the voter lists."""
    return (user.first_name or user.username or '').strip() or '(unknown)'


def _poll_voter_names(poll):
    """(yes_names, no_names, both_names) display-name lists for a poll, name-sorted."""
    def names(choice):
        return [
            _display_name(v.user)
            for v in poll.votes.filter(choice=choice)
            .select_related('user')
            .order_by('user__first_name', 'user__username')
        ]
    return names('yes'), names('no'), names('all')


def _handle_status(wa_message_id, phone, raw, reply=None):
    """Reply with the current open poll's vote counts and voter lists."""
    from apps.polls.models import Poll
    if reply is None:
        reply = _dm_sink(phone)

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        if _log_inbound(wa_message_id, phone, None, 'status', raw):
            reply(bot_messages.not_recognised())
        return

    if not _log_inbound(wa_message_id, phone, user, 'status', raw):
        return

    poll = _next_open_poll()
    if poll is None:
        reply(bot_messages.no_active_poll())
        return

    session = poll.session
    date_str = session.date.strftime("%a %d %b")
    yes_names, no_names, both_names = _poll_voter_names(poll)
    reply(bot_messages.status(
        session.name, date_str, yes_names, no_names, both_names,
        is_two_day=session.has_two_date_options,
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


def _handle_score(wa_message_id, phone, raw, reply=None):
    """Reply with live scores for the most relevant session.

    Picks today's session if there is one, else the most recent past session,
    else the next upcoming one. For each match in that session:
      - no innings yet → 'not started'
      - innings exist → totals derived from the Delivery ledger via scoring.innings_score
    """
    from apps.sessions.models import Session
    from apps.matches.scoring import innings_score
    if reply is None:
        reply = _dm_sink(phone)

    user = User.objects.filter(phone=phone).first()
    if user is None:
        if _log_inbound(wa_message_id, phone, None, 'score', raw):
            reply(bot_messages.not_recognised())
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
        reply(bot_messages.no_recent_session())
        return

    matches = list(
        session.matches
        .prefetch_related('innings__batting_team', 'teams')
        .order_by('id')
    )

    if not matches:
        date_str = session.date.strftime("%a %d %b")
        reply(bot_messages.match_not_started(session.name, date_str))
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
    reply(bot_messages.score(session.name, date_str, match_blocks))


def _handle_help(wa_message_id, phone, raw, reply=None):
    if reply is None:
        reply = _dm_sink(phone)

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        user = None

    if not _log_inbound(wa_message_id, phone, user, 'help', raw):
        return
    reply(bot_messages.help_text())


def _handle_unknown(wa_message_id, phone, text, raw, reply=None):
    """Reply when we couldn't parse the message. Echoes the user's input back
    (with the case they actually typed) so they can see what got through —
    helpful when mobile auto-capitalize or autocorrect mangled their RSVP.
    """
    if reply is None:
        reply = _dm_sink(phone)

    user = User.objects.filter(phone=phone).first()
    if not _log_inbound(wa_message_id, phone, user, 'unknown', {'raw': raw, 'text': text}):
        return

    safe_echo = text[:60] if text else ''
    reply(bot_messages.unknown(safe_echo))


def _check_bot_token(request, token_setting):
    """Validate ?token=… (or X-Bot-Token header) against the named setting.

    Shared by the read-only reminder URL (BOT_WEBHOOK_TOKEN) and the higher-trust
    group-inbound URL (BOT_INBOUND_TOKEN). Fails closed: a blank/unset expected
    token denies, so a Vote-writing endpoint can never go live unauthenticated.
    """
    expected = getattr(settings, token_setting, '')
    token = request.GET.get('token', '') or request.headers.get('X-Bot-Token', '')
    return bool(expected) and token == expected


def run_reminders_view(request):
    """Hit by an external scheduler (cron-job.org / GitHub Actions) every ~15 min.

    Auth via ?token=$BOT_WEBHOOK_TOKEN query string. Doubles as a Render keepalive.
    """
    if not _check_bot_token(request, 'BOT_WEBHOOK_TOKEN'):
        return _bad('unauthorized', 401)

    from .services import send_session_reminders
    counts = send_session_reminders()
    return JsonResponse({'ok': True, 'sent': counts})


# ─────────────────────────── Activity feed (in-app) ───────────────────────────

_DEFAULT_STYLE = KIND_STYLE[ActivityEvent.KIND_PING]


def _decorate(events, user, seen_before):
    """Attach row presentation + read-state to each event for
    the template. Own actions never show as unread (mirrors the bell count).

    RSVP rows are split visually: 'no' votes get the red-X style, 'yes' keeps
    the green check. Detected by ' is out of ' in the body — the signal that
    emits these events writes exactly that phrase for no votes (signals.on_vote),
    so the check is deterministic and avoids a DB hit on the GenericForeignKey.
    """
    for ev in events:
        style = KIND_STYLE.get(ev.kind, _DEFAULT_STYLE)
        if ev.kind == ActivityEvent.KIND_RSVP and ev.body and ' is out of ' in ev.body:
            style = RSVP_NO_STYLE
        ev.style = style
        ev.is_unread = ev.created_at > seen_before and ev.actor_id != user.id
    return events


def _feed_events(user, tab, seen_before, limit=100):
    # No select_related('actor'): the row template never renders the actor, and
    # is_unread reads the actor_id FK column already on the row.
    qs = ActivityEvent.objects.all()
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
