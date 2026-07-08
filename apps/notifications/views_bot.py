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
from datetime import timedelta

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from . import views as nviews
from .models import BotEvent, OutboundMessage, WhatsAppIdentity

logger = logging.getLogger(__name__)

# A claimed row whose Node worker died mid-send is reclaimable after this long,
# so a crash-after-claim doesn't strand the message as 'claimed' forever.
CLAIM_RECLAIM_SECONDS = 90


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
    lid = ''.join(ch for ch in (data.get('lid') or '') if ch.isdigit())
    wa_name = (data.get('author_name') or '')[:100]
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

    # Passively stage every LID we see (with its latest display name) so admins
    # can map even members who never trigger the roster import.
    if lid:
        WhatsAppIdentity.objects.update_or_create(
            lid=lid, defaults={'name': wa_name} if wa_name else {},
        )

    # Normalise reactions / poll votes into the vote text the dispatcher parses.
    if kind == 'reaction':
        choice = _REACTION_CHOICE.get(_normalize_emoji(data.get('emoji', '')))
        if choice is None:
            return JsonResponse({'ok': True, 'ignored': 'non_vote_reaction'})
        if choice == 'yes':
            text = 'Saturday'
        elif choice == 'no':
            poll = nviews._next_open_poll()
            text = 'Out' if poll and poll.session.has_two_date_options else 'No'
        else:
            text = 'Both'
    elif kind == 'poll_vote':
        selected = data.get('selected') or []
        if not selected:
            # Deselection / withdrawal — handled in Phase 2 (vote retract).
            return JsonResponse({'ok': True, 'ignored': 'poll_deselect'})
        selected_text = str(selected[0]).strip().lower()
        if selected_text.startswith(('not available', 'unavailable', 'out', 'na')):
            text = 'Out'
        elif selected_text.startswith(('sat', 'yes')):
            text = 'Saturday'
        elif selected_text.startswith(('sun', 'no')):
            text = 'Sunday'
        elif selected_text.startswith(('both', 'all')):
            text = 'Both'
        else:
            text = str(selected[0])
    else:
        text = (data.get('text') or '').strip()

    raw = {'source': 'group_bot', 'kind': kind, 'chat': chat, 'payload': data}
    reply = _enqueue_group_reply(target)
    # Only reactions (on the bot's message) and native poll votes count as RSVPs.
    # Typed 'yes'/'no' in the group is normal conversation — NOT a vote — so text
    # is dispatched with allow_text_rsvp=False (commands still work). The group
    # never gets an "I didn't understand" reply (reply_unknown=False).
    is_vote = kind in ('reaction', 'poll_vote')
    result = nviews.dispatch_inbound(
        wa_message_id, phone, text, chat='community', reply=reply, raw=raw,
        allow_text_rsvp=is_vote, reply_unknown=False, lid=lid, wa_name=wa_name,
    )

    actions = []
    if result and result.get('kind') == 'rsvp' and result.get('recorded'):
        if result.get('choice') == 'out':
            emoji = '❌'
        elif result.get('choice') == 'all':
            emoji = '☑️'
        elif result.get('choice') == 'no' and not result.get('is_two_day'):
            emoji = '❌'
        else:
            emoji = '✅'
        actions.append({
            'type': 'react',
            'emoji': emoji,
            'message_id': wa_message_id,
        })

    return JsonResponse({'ok': True, 'result': result, 'actions': actions})


@csrf_exempt
@require_POST
def roster_import(request):
    """Bulk-import the group's members as (lid, name) so admins can map them all
    at once, without waiting for each to vote. Auth: ?token=$BOT_WEBHOOK_TOKEN.
    Body: {members: [{lid, name}, ...]}. Upserts WhatsAppIdentity rows (keeps the
    existing user mapping; refreshes the name)."""
    if not nviews._check_bot_token(request, 'BOT_WEBHOOK_TOKEN'):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=401)
    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'bad json'}, status=400)

    from django.contrib.auth import get_user_model
    User = get_user_model()

    linked = 0   # phone matched a user → wa_name set (enables name-matched votes)
    staged = 0   # lid staged as a WhatsAppIdentity (manual-map fallback)
    for m in (data.get('members') or []):
        name = (m.get('name') or '')[:120]
        phone = nviews._normalize_inbound_phone(m.get('phone', ''))
        lid = ''.join(ch for ch in (m.get('lid') or '') if ch.isdigit())
        if phone and name:
            u = User.objects.filter(phone=phone).first()
            if u and u.wa_name != name:
                u.wa_name = name
                u.save(update_fields=['wa_name'])
                linked += 1
        if lid:
            WhatsAppIdentity.objects.update_or_create(
                lid=lid, defaults={'name': name} if name else {},
            )
            staged += 1
    return JsonResponse({'ok': True, 'linked': linked, 'staged': staged})


@csrf_exempt
def outbound_drain(request):
    """The Node bot pulls pending group posts here, claims them, and posts them.

    Auth: ?token=$BOT_WEBHOOK_TOKEN (read/queue token — outbound posts don't write
    Votes, so they use the lower-trust token, not BOT_INBOUND_TOKEN).

    Claims up to `limit` rows in one atomic, row-locked batch (skip_locked so
    concurrent drains never block each other): each PENDING row — or a CLAIMED row
    stuck past CLAIM_RECLAIM_SECONDS (worker died mid-send) — flips to CLAIMED with
    a fresh claimed_at. Claiming as a *status* (not just stamping claimed_at) is
    what stops a second drain from re-handing the same row out.
    """
    if not nviews._check_bot_token(request, 'BOT_WEBHOOK_TOKEN'):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=401)

    try:
        limit = max(1, min(int(request.GET.get('limit', 10)), 50))
    except (TypeError, ValueError):
        limit = 10

    reclaim_cutoff = timezone.now() - timedelta(seconds=CLAIM_RECLAIM_SECONDS)
    claimed = []
    with transaction.atomic():
        rows = list(
            OutboundMessage.objects
            .select_for_update(skip_locked=True)
            .filter(
                Q(status=OutboundMessage.PENDING)
                | Q(status=OutboundMessage.CLAIMED, claimed_at__lt=reclaim_cutoff)
            )
            .order_by('created_at')[:limit]
        )
        now = timezone.now()
        for r in rows:
            r.status = OutboundMessage.CLAIMED
            r.claimed_at = now
            r.save(update_fields=['status', 'claimed_at'])
            claimed.append({
                'id': r.id, 'kind': r.kind, 'body': r.body,
                'poll_options': r.poll_options, 'target': r.target,
            })

    return JsonResponse({'ok': True, 'messages': claimed})


@csrf_exempt
@require_POST
def outbound_ack(request):
    """The Node bot reports the outcome of a claimed post.

    Auth: ?token=$BOT_WEBHOOK_TOKEN. Body: {id, status:'sent', wa_message_id}
    → SENT (+ an outbound BotEvent for the audit log); {id, status:'failed', error}
    → FAILED with attempts incremented (a Phase 3 sweep re-queues attempts<3).
    """
    if not nviews._check_bot_token(request, 'BOT_WEBHOOK_TOKEN'):
        return JsonResponse({'ok': False, 'error': 'unauthorized'}, status=401)

    try:
        data = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({'ok': False, 'error': 'bad json'}, status=400)

    try:
        msg = OutboundMessage.objects.get(id=data.get('id'))
    except (OutboundMessage.DoesNotExist, ValueError, TypeError):
        return JsonResponse({'ok': False, 'error': 'not found'}, status=404)

    status = (data.get('status') or '').lower()
    if status == 'sent':
        msg.status = OutboundMessage.SENT
        msg.sent_at = timezone.now()
        msg.wa_message_id = (data.get('wa_message_id') or '')[:255]
        msg.save(update_fields=['status', 'sent_at', 'wa_message_id'])
        try:
            BotEvent.objects.create(
                wa_message_id=f"outbound:{msg.id}",
                phone='', user=None, action='group_post',
                direction=BotEvent.OUTBOUND,
                payload={'outbound_id': msg.id, 'target': msg.target,
                         'wa_message_id': msg.wa_message_id},
            )
        except IntegrityError:
            pass  # duplicate ack — already audited
    elif status == 'failed':
        msg.status = OutboundMessage.FAILED
        msg.error = (data.get('error') or '')[:255]
        msg.attempts = (msg.attempts or 0) + 1
        msg.save(update_fields=['status', 'error', 'attempts'])
    else:
        return JsonResponse({'ok': False, 'error': 'bad status'}, status=400)

    return JsonResponse({'ok': True, 'id': msg.id, 'status': msg.status})
