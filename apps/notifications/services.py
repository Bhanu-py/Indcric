import logging
from datetime import datetime, timedelta

import requests
from django.conf import settings
from django.db import IntegrityError
from django.utils import timezone

from .models import BotEvent

logger = logging.getLogger(__name__)

GRAPH_URL = "https://graph.facebook.com/v25.0/{phone_number_id}/messages"


def _graph_url():
    return GRAPH_URL.format(phone_number_id=settings.WHATSAPP_PHONE_NUMBER_ID)


def _headers():
    return {
        "Authorization": f"Bearer {settings.WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }


def send_template_message(to_phone, template_name, language_code="en_US", components=None):
    if not settings.WHATSAPP_PHONE_NUMBER_ID or not settings.WHATSAPP_ACCESS_TOKEN:
        logger.warning("WhatsApp credentials not configured — skipping DM to %s", to_phone)
        return False

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
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("WhatsApp send failed to %s: %s", to_phone, e)
        return False


def send_text_message(to_phone, text):
    if not settings.WHATSAPP_PHONE_NUMBER_ID or not settings.WHATSAPP_ACCESS_TOKEN:
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
        resp.raise_for_status()
        return True
    except requests.RequestException as e:
        logger.error("WhatsApp send failed to %s: %s", to_phone, e)
        return False


def notify_poll_created(poll):
    """
    DM all club members with a phone number when a new poll opens.
    Template body: "Hi {{1}}! New IndCric session: {{2}} on {{3}}. Reply YES to play or NO to sit out."
    """
    from django.contrib.auth import get_user_model
    User = get_user_model()

    session = poll.session
    date_str = session.date.strftime("%a %d %b")
    users_with_phone = User.objects.filter(phone__isnull=False).exclude(phone='')

    sent = 0
    for user in users_with_phone:
        components = [
            {
                "type": "body",
                "parameters": [
                    {"type": "text", "text": user.username},
                    {"type": "text", "text": session.name},
                    {"type": "text", "text": date_str},
                ],
            }
        ]
        ok = send_template_message(user.phone, "session_rsvp", components=components)
        if ok:
            sent += 1

    logger.info(
        "Poll created for session %s — notified %d/%d members",
        session.name, sent, users_with_phone.count()
    )
    return sent


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
