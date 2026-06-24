from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils import timezone


class BotEvent(models.Model):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'
    DIRECTION_CHOICES = [(INBOUND, 'Inbound'), (OUTBOUND, 'Outbound')]

    # 255, not 100: WhatsApp's multi-device '…@lid' ids are long, and the group
    # bot composes longer composite keys (e.g. 'pollvote:<msgId>:<voter>:<sel>').
    wa_message_id = models.CharField(max_length=255, unique=True)
    phone = models.CharField(max_length=20)
    user = models.ForeignKey(
        'accounts.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bot_events',
    )
    action = models.CharField(max_length=50)
    direction = models.CharField(max_length=10, choices=DIRECTION_CHOICES)
    payload = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.direction} {self.action} from {self.phone} at {self.created_at:%Y-%m-%d %H:%M}"


class OutboundMessage(models.Model):
    """Queue of messages the group-resident bot should post into a WhatsApp group.

    Django is the source of truth and only enqueues; the always-on Node
    (whatsapp-web.js) bot pulls `pending` rows, posts them, and acks. `BotEvent`
    stays the audit log — it has no status/claim fields and can't be the queue.

    `dedup_key` (e.g. ``poll_opened:{poll.id}``) is partial-unique so re-saves
    enqueue at most once. ``claimed`` (distinct from a bare `claimed_at` stamp) is
    what lets the drainer reclaim crashed-mid-send rows without double-posting.
    See .claude/features/whatsapp-group-bot.md.
    """
    PENDING, CLAIMED, SENT, FAILED = 'pending', 'claimed', 'sent', 'failed'
    STATUS_CHOICES = [
        (PENDING, 'Pending'), (CLAIMED, 'Claimed'),
        (SENT, 'Sent'), (FAILED, 'Failed'),
    ]
    TEXT, POLL = 'text', 'poll'
    KIND_CHOICES = [(TEXT, 'Text'), (POLL, 'Poll')]

    # 'text' = a plain message; 'poll' = a native WhatsApp poll, where `body` is
    # the question and `poll_options` are the choices the Node bot posts.
    kind = models.CharField(max_length=8, choices=KIND_CHOICES, default=TEXT)
    body = models.TextField()
    poll_options = models.JSONField(default=list, blank=True)
    # Group JID or an alias the Node bot resolves to a JID ('community' default).
    target = models.CharField(max_length=120, default='community')
    status = models.CharField(
        max_length=10, choices=STATUS_CHOICES, default=PENDING, db_index=True,
    )
    dedup_key = models.CharField(max_length=80, blank=True, default='')
    claimed_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    wa_message_id = models.CharField(max_length=255, blank=True, default='')
    error = models.CharField(max_length=255, blank=True, default='')
    attempts = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        constraints = [
            models.UniqueConstraint(
                fields=['dedup_key'],
                condition=~models.Q(dedup_key=''),
                name='uniq_outbound_dedup',
            ),
        ]

    def __str__(self):
        return f"[{self.status}] → {self.target}: {self.body[:40]}"


class WhatsAppIdentity(models.Model):
    """A WhatsApp group member discovered by LID.

    In Community / privacy-on groups the bot sees only an opaque '<lid>@lid' and
    the member's display name — never the phone — so members can't be matched by
    number. Each discovered (lid, name) is staged here; an admin maps it to a
    User, and saving mirrors the lid onto User.wa_lid so group votes start
    matching. Populated by the roster import (/api/bot/roster/) and passively as
    members vote/react. See whatsapp-group-bot.md 'Identity'.
    """
    lid = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=120, blank=True, default='')
    user = models.ForeignKey(
        'accounts.User', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='wa_identities',
    )
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['user_id', 'name']
        verbose_name = 'WhatsApp identity'
        verbose_name_plural = 'WhatsApp identities'

    def __str__(self):
        return f"{self.name or '(no name)'} [{self.lid}]"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        # Mirror the mapping onto the user so inbound matching (User.wa_lid) works.
        # .update() avoids re-triggering signals / recursion.
        if self.user_id and self.lid:
            from django.contrib.auth import get_user_model
            get_user_model().objects.filter(pk=self.user_id).update(wa_lid=self.lid)


class ActivityEvent(models.Model):
    """One entry in the club-wide activity feed (the design's Notifications /
    Activity screen). The feed is GLOBAL — every member sees the same timeline;
    per-user read state lives in :class:`ActivityFeedState`.

    Events are emitted by signal receivers in ``signals.py`` when things happen
    elsewhere (a donation lands, a session is created/confirmed, a match
    finishes, a payment is received). ``kind`` drives the row's icon/colour and
    which tab it falls under; the optional generic ``target`` links back to the
    source object and lets emitters dedupe (one match-result row per match).
    """
    KIND_SESSION = 'session'
    KIND_RSVP = 'rsvp'
    KIND_PAYMENT = 'payment'
    KIND_MATCH = 'match'
    KIND_MENTION = 'mention'
    KIND_DONATION = 'donation'
    KIND_TEAM = 'team'
    KIND_PING = 'ping'
    KIND_CHOICES = [
        (KIND_SESSION, 'Session'),
        (KIND_RSVP, 'RSVP'),
        (KIND_PAYMENT, 'Payment'),
        (KIND_MATCH, 'Match'),
        (KIND_MENTION, 'Mention'),
        (KIND_DONATION, 'Donation'),
        (KIND_TEAM, 'Team'),
        (KIND_PING, 'Ping'),
    ]

    kind = models.CharField(max_length=12, choices=KIND_CHOICES)
    # Who triggered it (NULL for system/anonymous, e.g. an anonymous donation).
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL,
        null=True, blank=True, related_name='activity_events',
    )
    body = models.CharField(max_length=255)
    # Small mono context shown after the timestamp (e.g. the session name).
    context = models.CharField(max_length=120, blank=True)
    url = models.CharField(max_length=300, blank=True, help_text="Where the row links to.")
    action_label = models.CharField(
        max_length=30, blank=True, help_text="Optional row CTA, e.g. 'View' / 'Pay' / 'RSVP'."
    )

    # Optional link back to the source object — used for dedupe and future
    # filtering. SET_NULL via content-type so a deleted source doesn't cascade
    # the feed entry away.
    content_type = models.ForeignKey(
        ContentType, on_delete=models.SET_NULL, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')

    # Idempotency key for state-change events (match result, payment received):
    # blank for ordinary one-shot rows, "{kind}:{ct}:{oid}" for deduped ones. The
    # partial unique constraint makes 'one row per (kind, target)' race-safe, and
    # emit() update_or_create's on it so a corrected event (e.g. a re-finalized
    # winner) refreshes the existing row instead of leaving a stale one.
    dedup_key = models.CharField(max_length=64, blank=True, default='')

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['content_type', 'object_id']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['dedup_key'],
                condition=~models.Q(dedup_key=''),
                name='uniq_activity_dedup_key',
            ),
        ]

    def __str__(self):
        return f"[{self.kind}] {self.body}"

    @property
    def safe_url(self):
        """Render-safe link target — only same-origin paths or http(s) URLs.
        Blocks javascript:/data: schemes that survive HTML autoescaping. All
        emitted urls come from reverse() (leading '/'), so this is a guard
        against an admin-edited or future caller's hostile value."""
        u = self.url or ''
        if u.startswith('/') or u.startswith('https://') or u.startswith('http://'):
            return u
        return ''


class ActivityFeedState(models.Model):
    """Per-user 'last seen' marker for the activity feed. The unread badge counts
    events created after ``last_seen_at`` (excluding the user's own actions); a
    single timestamp gives both the bell count and the per-row unread dots
    without a row-per-notification table."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_state'
    )
    last_seen_at = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.user} last saw activity at {self.last_seen_at:%Y-%m-%d %H:%M}"


def seen_at_for(user):
    """The user's activity-feed 'last seen' time. Falls back to when they joined
    so a brand-new state shows recent club activity as unread (not everything
    ever)."""
    state = ActivityFeedState.objects.filter(user=user).only('last_seen_at').first()
    if state:
        return state.last_seen_at
    return user.date_joined


def unread_count_for(user):
    """Number of feed events the user hasn't seen yet, excluding their own
    actions (you don't need a badge for your own donation)."""
    if not getattr(user, 'is_authenticated', False):
        return 0
    return (
        ActivityEvent.objects
        .filter(created_at__gt=seen_at_for(user))
        .exclude(actor=user)
        .count()
    )
