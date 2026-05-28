import logging
import urllib.parse
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.db import IntegrityError
from django.urls import reverse
from django.utils import timezone

from .models import BotEvent

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v25.0/{phone_number_id}/messages"


def _whatsapp_configured():
    return bool(settings.WHATSAPP_PHONE_NUMBER_ID and settings.WHATSAPP_ACCESS_TOKEN)


def _graph_url():
    return GRAPH_URL.format(phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID)


def _headers():
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def _log_meta_error(to_phone, resp):
    """Pull the (#code) message out of Meta's JSON error body, not just the HTTP code."""
    try:
        err = resp.json().get("error", {})
        # Meta's `message` already contains the (#code) prefix; don't re-prepend.
        msg = err.get("message") or err.get("error_data", {}).get("details", "")
        logger.error("WhatsApp send failed to %s: HTTP %s — %s",
                     to_phone, resp.status_code, msg)
    except Exception:
        logger.error("WhatsApp send failed to %s: HTTP %s — %s",
                     to_phone, resp.status_code, resp.text[:300])


def send_template_message(to_phone, template_name, language_code=None, components=None):
    if not _whatsapp_configured():
        logger.warning("WhatsApp credentials not configured — skipping DM to %s", to_phone)
        return False

    if language_code is None:
        language_code = getattr(settings, 'WHATSAPP_TEMPLATE_LANGUAGE', 'en_US')

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {"code": language_code},
        },
    }
    if components:
        payload["template"]["components"] = components

    try:
        resp = requests.post(_graph_url(), headers=_headers(), json=payload, timeout=10)
        if not resp.ok:
            _log_meta_error(to_phone, resp)
            return False
        return True
    except requests.RequestException as e:
        logger.error("WhatsApp send failed to %s: %s", to_phone, e)
        return False


def send_text_message(to_phone, text):
    if not _whatsapp_configured():
        logger.warning("WhatsApp credentials not configured — skipping DM to %s", to_phone)
        return False

    payload = {
        "messaging_product": "whatsapp",
        "to": to_phone,
        "type": "text",
        "text": {"body": text},
    }

    try:
        resp = requests.post(_graph_url(), headers=_headers(), json=payload, timeout=10)
        if not resp.ok:
            _log_meta_error(to_phone, resp)
            return False
        return True
    except requests.RequestException as e:
        logger.error("WhatsApp send failed to %s: %s", to_phone, e)
        return False


def _build_rsvp_components(user, session):
    """Components payload for the session_rsvp template.

    Template body:  "Hi {{1}}! New IndCric session: {{2}} on {{3}}. Reply YES to play or NO to sit out."
    URL button:     https://indcric.onrender.com/session/{{1}}/   (button {{1}} = session id)
    """
    date_str = session.date.strftime("%a %d %b")
    return [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": user.username},
                {"type": "text", "text": session.name},
                {"type": "text", "text": date_str},
            ],
        },
        {
            "type": "button",
            "sub_type": "url",
            "index": "0",
            "parameters": [
                {"type": "text", "text": str(session.id)},
            ],
        },
    ]


def _send_rsvp_invite(user, poll, attempt):
    """Send one RSVP template DM and log a BotEvent. Returns True on send success.

    `attempt` is the next sequence number for this (poll, user). The BotEvent's
    wa_message_id is `rsvp_invite:{poll_id}:{user_id}:{attempt}` — unique per
    attempt so retries don't trip the idempotency constraint.
    """
    session = poll.session
    wa_id = f"rsvp_invite:{poll.id}:{user.id}:{attempt}"
    try:
        BotEvent.objects.create(
            wa_message_id=wa_id,
            phone=user.phone,
            user=user,
            action='rsvp_invite',
            direction=BotEvent.OUTBOUND,
            payload={'session_id': session.id, 'poll_id': poll.id, 'attempt': attempt},
        )
    except IntegrityError:
        return False

    components = _build_rsvp_components(user, session)
    ok = send_template_message(user.phone, settings.WHATSAPP_RSVP_TEMPLATE, components=components)
    if not ok:
        BotEvent.objects.filter(wa_message_id=wa_id).delete()
        return False
    return True


def _next_attempt(poll_id, user_id):
    """Return the next attempt index for this (poll, user) based on prior BotEvents."""
    prefix = f"rsvp_invite:{poll_id}:{user_id}:"
    existing = BotEvent.objects.filter(
        wa_message_id__startswith=prefix,
        action='rsvp_invite',
    ).count()
    return existing + 1


def notify_poll_created(poll):
    """DM all club members with a phone number when a new poll opens.

    Logs a BotEvent per send so we know who got the original invite.
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    users_with_phone = User.objects.filter(phone__isnull=False).exclude(phone='')

    sent = 0
    for user in users_with_phone:
        attempt = _next_attempt(poll.id, user.id)
        if _send_rsvp_invite(user, poll, attempt):
            sent += 1

    logger.info(
        "Poll created for session %s — notified %d/%d members",
        poll.session.name, sent, users_with_phone.count()
    )
    return sent


SCOPE_NON_VOTERS = 'non_voters'
SCOPE_ALL = 'all'
RESEND_COOLDOWN_HOURS = 6


def resend_poll_invite(poll, scope=SCOPE_NON_VOTERS, cooldown_hours=RESEND_COOLDOWN_HOURS):
    """Re-fire the session_rsvp template to selected club members.

    scope='non_voters' (default) skips users who already have a Vote on this poll.
    scope='all' targets every phone-having member.

    Per (poll, user), enforce a `cooldown_hours` gap since the last rsvp_invite
    BotEvent — prevents accidental spam from double-clicks. Returns a counts dict.
    """
    from django.contrib.auth import get_user_model
    from apps.polls.models import Vote
    User = get_user_model()

    targets = User.objects.filter(phone__isnull=False).exclude(phone='')
    if scope == SCOPE_NON_VOTERS:
        voted_ids = set(Vote.objects.filter(poll=poll).values_list('user_id', flat=True))
        targets = targets.exclude(id__in=voted_ids)
    elif scope != SCOPE_ALL:
        raise ValueError(f"Unknown resend scope: {scope!r}")

    target_count = targets.count()
    counts = {
        'sent': 0,
        'skipped_cooldown': 0,
        'skipped_no_creds': 0,
        'failed': 0,
        'targets': target_count,
    }

    if not _whatsapp_configured():
        logger.warning(
            "Resend poll %s (scope=%s) — WhatsApp credentials not configured, "
            "skipping %d target(s)", poll.id, scope, target_count,
        )
        counts['skipped_no_creds'] = target_count
        return counts

    cutoff = timezone.now() - timedelta(hours=cooldown_hours)

    for user in targets:
        prefix = f"rsvp_invite:{poll.id}:{user.id}:"
        last_invite_at = (
            BotEvent.objects
            .filter(wa_message_id__startswith=prefix, action='rsvp_invite')
            .order_by('-created_at')
            .values_list('created_at', flat=True)
            .first()
        )
        if last_invite_at and last_invite_at >= cutoff:
            counts['skipped_cooldown'] += 1
            continue

        attempt = _next_attempt(poll.id, user.id)
        if _send_rsvp_invite(user, poll, attempt):
            counts['sent'] += 1
        else:
            counts['failed'] += 1

    logger.info(
        "Resend poll %s (scope=%s) — sent=%d skipped_cooldown=%d failed=%d (of %d targets)",
        poll.id, scope, counts['sent'], counts['skipped_cooldown'],
        counts['failed'], target_count,
    )
    return counts


REMINDER_KINDS = ('reminder_24h', 'reminder_morning', 'reminder_2h')
_REMINDER_LABELS = {
    'reminder_24h': 'tomorrow',
    'reminder_morning': 'today',
    'reminder_2h': 'in 2 hours',
}


def _session_start_dt(session):
    naive = datetime.combine(session.date, session.time)
    return timezone.make_aware(naive, timezone.get_current_timezone())


def _due_kinds(session_dt, now):
    delta = session_dt - now
    due = []
    if timedelta(hours=18) <= delta <= timedelta(hours=25):
        due.append('reminder_24h')
    local_now = timezone.localtime(now)
    local_session = timezone.localtime(session_dt)
    if (local_now.date() == local_session.date()
            and local_now.hour >= 8
            and delta >= timedelta(hours=3)):
        due.append('reminder_morning')
    if timedelta(hours=1) <= delta <= timedelta(hours=3):
        due.append('reminder_2h')
    return due


def _notify_one_reminder(session, user, kind, label):
    template = getattr(settings, 'WHATSAPP_REMINDER_TEMPLATE', '')
    if not template:
        return False

    wa_id = f"reminder:{session.id}:{user.id}:{kind}"
    try:
        BotEvent.objects.create(
            wa_message_id=wa_id,
            phone=user.phone,
            user=user,
            action=kind,
            direction=BotEvent.OUTBOUND,
            payload={'session_id': session.id, 'kind': kind, 'label': label},
        )
    except IntegrityError:
        return False

    date_str = session.date.strftime("%a %d %b")
    time_str = session.time.strftime("%H:%M")
    components = [
        {
            "type": "body",
            "parameters": [
                {"type": "text", "text": user.username},
                {"type": "text", "text": session.name},
                {"type": "text", "text": f"{date_str} {time_str}"},
                {"type": "text", "text": label},
            ],
        }
    ]
    ok = send_template_message(user.phone, template, components=components)
    if not ok:
        # Let the next tick retry — delete the idempotency row.
        BotEvent.objects.filter(wa_message_id=wa_id).delete()
        return False
    return True


def send_session_reminders():
    """Send DM reminders for upcoming sessions. Idempotent — safe to call repeatedly.

    Returns a dict of {kind: send_count}.
    """
    from django.contrib.auth import get_user_model
    from apps.sessions.models import Session
    User = get_user_model()

    if not getattr(settings, 'WHATSAPP_REMINDER_TEMPLATE', ''):
        logger.info("WHATSAPP_REMINDER_TEMPLATE not configured — skipping reminder run")
        return {kind: 0 for kind in REMINDER_KINDS}

    now = timezone.now()
    horizon_date = (now + timedelta(hours=26)).date()
    upcoming = Session.objects.filter(date__gte=now.date(), date__lte=horizon_date)

    users_with_phone = list(User.objects.filter(phone__isnull=False).exclude(phone=''))
    counts = {kind: 0 for kind in REMINDER_KINDS}

    for session in upcoming:
        try:
            session_dt = _session_start_dt(session)
        except (ValueError, TypeError):
            logger.warning("Skipping session %s — invalid date/time", session.id)
            continue
        if session_dt <= now:
            continue

        for kind in _due_kinds(session_dt, now):
            label = _REMINDER_LABELS[kind]
            for user in users_with_phone:
                if _notify_one_reminder(session, user, kind, label):
                    counts[kind] += 1

    return counts


# ─────────────────────────────────────────────────────────────────────────────
# Group-share helpers (free path: admin pastes a formatted message into the
# WhatsApp Community group; members tap wa.me deep links to RSVP, which opens
# a free 24-hour service window for the bot to receive their reply).
# ─────────────────────────────────────────────────────────────────────────────

def _bot_number_for_walink():
    """Bot's phone number stripped to digits only — the format wa.me expects.

    Accepts whatever the admin pasted in WHATSAPP_BOT_NUMBER (with or without
    '+', with or without spaces/dashes/parens) and keeps only digits, so a
    sloppy env value like '+91 7330 7132' becomes '9173307132'. Returns ''
    if no number is set (caller hides the share button in that case).
    """
    raw = getattr(settings, 'WHATSAPP_BOT_NUMBER', '') or ''
    return ''.join(ch for ch in raw if ch.isdigit())


def build_group_invite_text(poll, base_url):
    """Compose the message an admin will paste into the WhatsApp group.

    Includes wa.me deep links per choice — tapping YES opens the bot DM with
    'YES <session_id>' pre-filled. When the user sends, the inbound webhook
    parses the session id and records the vote, all inside the free 24h
    service window opened by their message.

    Falls back to instructions + website link if WHATSAPP_BOT_NUMBER isn't set.
    """
    session = poll.session
    date_str = session.date.strftime("%a %d %b")
    time_str = session.time.strftime("%H:%M") if session.time else ''
    session_url = base_url.rstrip('/') + reverse('session_detail', args=[session.id])
    bot = _bot_number_for_walink()

    lines = [
        f"🏏 ICG session — {session.name}",
        f"📅 {date_str}" + (f" · {time_str}" if time_str else ''),
        f"📍 {session.location}",
    ]
    if session.cost:
        lines.append(f"💰 €{session.cost} total")
    lines.append("")

    if bot:
        lines.append("RSVP by tapping below — the bot will record your vote:")
        lines.append(f"✅ YES → https://wa.me/{bot}?text=YES%20{session.id}")
        lines.append(f"❌ NO → https://wa.me/{bot}?text=NO%20{session.id}")
    else:
        lines.append("Vote on the website (link below).")

    lines.append("")
    lines.append(f"Details: {session_url}")
    return "\n".join(lines)


def build_group_share_url(poll, base_url):
    """wa.me/?text=... URL that opens the admin's WhatsApp share picker.

    Tapping this on the admin's phone opens WhatsApp with the formatted invite
    text pre-composed; they pick the Community group and send. Returns an empty
    string if there's no session/poll to share.
    """
    if poll is None:
        return ''
    text = build_group_invite_text(poll, base_url)
    return "https://wa.me/?text=" + urllib.parse.quote(text, safe='')
