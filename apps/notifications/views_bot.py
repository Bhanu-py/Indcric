"""Group-resident bot endpoints (Phase 1: inbound).

The always-on Node (whatsapp-web.js) bot POSTs members' group activity — typed
messages, emoji reactions, and native-poll votes — to /api/bot/inbound/. We
translate reactions/poll-votes into the canonical YES/NO the shared
``dispatch_inbound`` already parses, record the Vote, and tell the bot to react
✅/❌ to the member's message (command replies are queued as text instead).

Phase 2 will add outbound_drain / outbound_ack here so the bot can pull and post
queued OutboundMessage rows. See .claude/features/whatsapp-group-bot.md.
"""
import json
import logging

from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import views as nviews
from .models import OutboundMessage

logger = logging.getLogger(__name__)


def _enqueue_group_reply(target):
    """Reply sink for the group path: enqueue an OutboundMessage the Node bot
    will post. Used for command replies (HELP/STATUS/BALANCE/unknown) — RSVP
    confirmations are emoji reactions returned in the response, not queued text
    (a per-vote text post would flood the group)."""
    def _sink(text):
        OutboundMessage.objects.create(body=text, target=target)
    return _sink


def _normalize_emoji(emoji):
    """Strip skin-tone modifiers (U+1F3FB–U+1F3FF) and the U+FE0F variation
    selector so '👍🏾' compares equal to '👍'. The Phase 0 spike found a
    skin-toned thumbs-up silently dropped because of a bare equality check."""
    return ''.join(
        ch for ch in (emoji or '')
        if not (0x1F3FB <= ord(ch) <= 0x1F3FF) and ord(ch) != 0xFE0F
    )


_REACTION_CHOICE = {'👍': 'yes', '👎': 'no', '✅': 'yes', '❌': 'no'}


def _bot_digits():
    return ''.join(ch for ch in (getattr(settings, 'WHATSAPP_BOT_NUMBER', '') or '') if ch.isdigit())


@csrf_exempt
@require_POST
def inbound_message(request):
    """Record group activity forwarded by the Node bot.

    Auth: ?token=$BOT_INBOUND_TOKEN (separate, higher-trust — this WRITES votes).
    Body JSON: {from, wa_message_id, text, chat, author_name, kind, emoji?, selected?}
      kind: 'text' (default) | 'reaction' | 'poll_vote'
    Always returns 200 on duplicate deliveries (idempotent via BotEvent's unique
    wa_message_id). Returns {actions: [...]} telling the bot to react ✅/❌.
    """
    if not nviews._check_bot_token(request, 'BOT_INBOUND_TOKEN'):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'bad json'}, status=400)

    wa_message_id = (data.get('wa_message_id') or '').strip()
    phone = nviews._normalize_inbound_phone(data.get('from', ''))
    chat = data.get('chat') or 'community'
    target = data.get('target') or 'community'
    kind = (data.get('kind') or 'text').lower()

    if not wa_message_id or not phone:
        return JsonResponse({'ok': False, 'error': 'missing from/wa_message_id'}, status=400)

    # Ignore the bot's own echoed activity — it sees its own ✅/❌ confirmation
    # reactions come back through the same listener.
    bot = _bot_digits()
    if bot and phone.lstrip('+') == bot:
        return JsonResponse({'ok': True, 'ignored': 'self'})

    # Normalise reactions / poll votes into the YES/NO text the dispatcher parses.
    if kind == 'reaction':
        choice = _REACTION_CHOICE.get(_normalize_emoji(data.get('emoji', '')))
        if choice is None:
            return JsonResponse({'ok': True, 'ignored': 'non_vote_reaction'})
        text = 'YES' if choice == 'yes' else 'NO'
    elif kind == 'poll_vote':
        selected = data.get('selected') or []
        if not selected:
            # Deselection / withdrawal — handled in Phase 2 (vote retract).
            return JsonResponse({'ok': True, 'ignored': 'poll_deselect'})
        text = 'YES' if str(selected[0]).lower().startswith('yes') else 'NO'
    else:
        text = (data.get('text') or '').strip()

    raw = {'source': 'group_bot', 'kind': kind, 'chat': chat, 'payload': data}
    reply = _enqueue_group_reply(target)
    result = nviews.dispatch_inbound(
        wa_message_id, phone, text, chat='community', reply=reply, raw=raw,
    )

    actions = []
    if result and result.get('kind') == 'rsvp' and result.get('recorded'):
        actions.append({
            'type': 'react',
            'emoji': '✅' if result.get('choice') == 'yes' else '❌',
            'message_id': wa_message_id,
        })

    return JsonResponse({'ok': True, 'result': result, 'actions': actions})
