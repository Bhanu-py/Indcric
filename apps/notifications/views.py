import hashlib
import hmac
import json
import logging
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model

from .models import BotEvent

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
    """Pull a comparable text token from text, button, or list-reply payloads."""
    msg_type = msg.get('type')
    if msg_type == 'text':
        return (msg.get('text', {}).get('body', '') or '').strip().lower()
    if msg_type == 'interactive':
        interactive = msg.get('interactive', {})
        sub = interactive.get('type')
        if sub == 'button_reply':
            br = interactive.get('button_reply', {})
            return (br.get('id') or br.get('title') or '').strip().lower()
        if sub == 'list_reply':
            lr = interactive.get('list_reply', {})
            return (lr.get('id') or lr.get('title') or '').strip().lower()
    if msg_type == 'button':
        return (msg.get('button', {}).get('text', '') or '').strip().lower()
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

    if text in ('yes', 'y', '✅', '1'):
        _handle_rsvp(wa_message_id, phone, 'yes', msg)
    elif text in ('no', 'n', '❌', '2'):
        _handle_rsvp(wa_message_id, phone, 'no', msg)
    elif text in ('balance', 'bal', '/balance', 'wallet'):
        _handle_balance(wa_message_id, phone, msg)
    elif text in ('help', '/help', '?'):
        _handle_help(wa_message_id, phone, msg)
    else:
        logger.info('Unrecognised WhatsApp message from %s: %s', phone, text)
        _handle_help(wa_message_id, phone, msg)


def _handle_rsvp(wa_message_id, phone, choice, raw):
    from apps.sessions.models import Session
    from apps.polls.models import Poll, Vote

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        logger.warning('WhatsApp RSVP from unknown phone %s', phone)
        try:
            BotEvent.objects.create(
                wa_message_id=wa_message_id, phone=phone, user=None,
                action='rsvp', direction=BotEvent.INBOUND, payload=raw,
            )
        except IntegrityError:
            pass
        return

    poll = (
        Session.objects
        .filter(poll__is_open=True)
        .order_by('-date')
        .values_list('poll', flat=True)
        .first()
    )
    if not poll:
        logger.info('No open poll for RSVP from %s', phone)
        return

    poll_obj = Poll.objects.get(pk=poll)
    try:
        with transaction.atomic():
            BotEvent.objects.create(
                wa_message_id=wa_message_id, phone=phone, user=user,
                action='rsvp', direction=BotEvent.INBOUND, payload=raw,
            )
            Vote.objects.update_or_create(
                poll=poll_obj, user=user, defaults={'choice': choice}
            )
    except IntegrityError:
        pass


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
            send_text_message(
                phone,
                "I don't recognise this number. Please add your WhatsApp number to your IndCric profile first."
            )
        return

    if not _log_inbound(wa_message_id, phone, user, 'balance', raw):
        return  # duplicate webhook

    wallet_total = Wallet.objects.filter(user=user).aggregate(s=Sum('amount'))['s'] or 0
    unpaid = (
        Payment.objects.filter(user=user, status='pending')
        .select_related('session')
        .order_by('session__date')
    )

    lines = [f"Wallet balance: €{wallet_total:.2f}"]
    if unpaid.exists():
        lines.append("")
        lines.append("Outstanding sessions:")
        for p in unpaid:
            lines.append(f"- {p.session.name}: €{p.amount:.2f}")
        total_due = sum((p.amount for p in unpaid), start=0)
        lines.append("")
        lines.append(f"Total due: €{total_due:.2f}")
    else:
        lines.append("No outstanding payments.")

    send_text_message(phone, "\n".join(lines))


def _handle_help(wa_message_id, phone, raw):
    from .services import send_text_message

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        user = None

    _log_inbound(wa_message_id, phone, user, 'help', raw)
    send_text_message(
        phone,
        "IndCric bot commands:\n"
        "- YES / NO: RSVP to the latest session poll\n"
        "- BALANCE: show wallet balance and outstanding payments\n"
        "- HELP: show this message"
    )


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
