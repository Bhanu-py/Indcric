import json
import logging
from django.conf import settings
from django.db import IntegrityError, transaction
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
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


def _handle_whatsapp_message(request):
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
    except Exception:
        logger.exception('Error processing WhatsApp webhook payload')

    return HttpResponse('OK', status=200)


def _process_message(msg, value):
    wa_message_id = msg.get('id', '')
    phone = msg.get('from', '')
    text = (msg.get('text', {}).get('body', '') or '').strip().lower()

    if msg.get('type') != 'text' or not text:
        return

    if text in ('yes', 'y', '✅', '1'):
        _handle_rsvp(wa_message_id, phone, 'yes', msg)
    elif text in ('no', 'n', '❌', '2'):
        _handle_rsvp(wa_message_id, phone, 'no', msg)
    else:
        logger.info('Unrecognised WhatsApp message from %s: %s', phone, text)


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


def _authenticate(request):
    token = request.headers.get('X-Bot-Token', '')
    expected = getattr(settings, 'BOT_WEBHOOK_TOKEN', '')
    return bool(expected) and token == expected


@csrf_exempt
@require_POST
def bot_rsvp_view(request):
    from apps.sessions.models import Session
    from apps.polls.models import Vote

    if not _authenticate(request):
        return _bad('unauthorized', 401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return _bad('invalid json')

    wa_message_id = data.get('wa_message_id', '').strip()
    phone = data.get('phone', '').strip()
    session_id = data.get('session_id')
    choice = data.get('choice', '').strip().lower()

    if not all([wa_message_id, phone, session_id, choice]):
        return _bad('missing fields: wa_message_id, phone, session_id, choice required')

    if choice not in ('yes', 'no'):
        return _bad('choice must be yes or no')

    try:
        user = User.objects.get(phone=phone)
    except User.DoesNotExist:
        try:
            BotEvent.objects.create(
                wa_message_id=wa_message_id, phone=phone, user=None,
                action='rsvp', direction=BotEvent.INBOUND, payload=data,
            )
        except IntegrityError:
            pass
        return _bad('user_not_found', 404)

    try:
        session = Session.objects.select_related('poll').get(pk=session_id)
    except Session.DoesNotExist:
        return _bad('session_not_found', 404)

    if not hasattr(session, 'poll'):
        return _bad('no_poll')

    poll = session.poll
    if not poll.is_open:
        return _bad('poll_closed')

    try:
        with transaction.atomic():
            BotEvent.objects.create(
                wa_message_id=wa_message_id, phone=phone, user=user,
                action='rsvp', direction=BotEvent.INBOUND, payload=data,
            )
            vote, created = Vote.objects.update_or_create(
                poll=poll, user=user, defaults={'choice': choice}
            )
    except IntegrityError:
        return JsonResponse({'ok': True, 'duplicate': True})

    return JsonResponse({'ok': True, 'created': created, 'choice': choice})
