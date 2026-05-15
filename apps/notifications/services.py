import logging
import requests
from django.conf import settings

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
