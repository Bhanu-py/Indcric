"""Feed emitters — translate domain events into ActivityEvent rows.

Connected in NotificationsConfig.ready(). Every emit goes through safe_emit,
which wraps the write in a savepoint so a feed failure is logged but never rolls
back the underlying save (a broken notification must not lose a donation or
payment — and on Postgres a swallowed exception alone wouldn't guarantee that).

Created-events (donation, new session, poll opened) fire on ``created=True``.
State-change events (session confirmed, match result, payment received) detect
the transition and dedupe on the source object (update_or_create) so a re-save
refreshes rather than double-posts.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone

from apps.donations.models import Donation
from apps.matches.models import Match
from apps.payments.models import Payment
from apps.polls.models import Poll
from apps.sessions.models import Session

from .activity import safe_emit
from .models import ActivityEvent


@receiver(post_save, sender=Donation)
def on_donation(sender, instance, created, **kwargs):
    """A donation landed — celebrate it on the wall. Respects anonymity: an
    anonymous gift shows 'Anonymous' (via display_name) and no actor link."""
    if not created:
        return
    campaign = instance.campaign.title if instance.campaign_id else "the club"
    actor = None if instance.is_anonymous else instance.user
    safe_emit(
        ActivityEvent.KIND_DONATION,
        f"{instance.display_name} donated €{instance.amount:.2f} to {campaign}",
        actor=actor,
        url=reverse('support'),
        action_label='View',
        context=campaign,
        target=instance,
    )


@receiver(pre_save, sender=Session)
def stash_session_confirmed(sender, instance, **kwargs):
    """Stash the pre-save attendance_confirmed so post_save can detect the
    False→True flip (a session being locked in)."""
    if instance.pk:
        old = sender.objects.filter(pk=instance.pk).only('attendance_confirmed').first()
        instance._old_confirmed = old.attendance_confirmed if old else None
    else:
        instance._old_confirmed = None


@receiver(post_save, sender=Session)
def on_session(sender, instance, created, **kwargs):
    if created:
        # Only an upcoming session is worth an 'RSVP' prompt; a back-filled past
        # session just gets a plain 'View'.
        upcoming = instance.date >= timezone.localdate()
        safe_emit(
            ActivityEvent.KIND_SESSION,
            f"New session: {instance.name} on {instance.date:%a %d %b}",
            actor=instance.created_by,
            url=instance.get_absolute_url(),
            action_label='RSVP' if upcoming else 'View',
            context=instance.location,
            target=instance,
        )
    elif (getattr(instance, '_old_confirmed', None) is False
          and instance.attendance_confirmed and instance.cost_per_person):
        # 'Confirm attendance' locks the roster and splits the cost — this is a
        # settlement / payments-due event (often for a past session), NOT a
        # forward-looking 'see you there'. Free sessions have nothing to split,
        # so they get no feed entry.
        safe_emit(
            ActivityEvent.KIND_PAYMENT,
            f"Cost split for {instance.name} ({instance.date:%a %d %b}) — "
            f"€{instance.cost_per_person:.2f} per player",
            actor=instance.created_by,
            url=instance.get_absolute_url(),
            action_label='View',
            context=instance.location,
            target=instance,
        )


@receiver(post_save, sender=Poll)
def on_poll(sender, instance, created, **kwargs):
    if not created:
        return
    session = instance.session
    safe_emit(
        ActivityEvent.KIND_SESSION,
        f"Poll opened — are you in for {session.name}?",
        url=session.get_absolute_url(),
        action_label='Vote',
        context=session.name,
        target=instance,
    )


@receiver(post_save, sender=Match)
def on_match(sender, instance, **kwargs):
    """Post the match result once the match is complete. Fires on the Match save
    that finalize_match_result() makes (winner already set), and refreshes the
    row if the match is reopened and re-finalized with a different result. While
    a match is reopened it isn't complete, so this early-returns and the last
    result stands until the new one is finalized."""
    if not instance.is_completed:
        return
    if instance.winner_id:
        body = f"{instance.winner.name} won {instance.name}"
    else:
        body = f"{instance.name} ended in a tie"
    safe_emit(
        ActivityEvent.KIND_MATCH,
        body,
        url=reverse('match_detail', args=[instance.pk]),
        action_label='View',
        context=instance.session.name if instance.session_id else '',
        target=instance,
        dedup=True,
    )


@receiver(post_save, sender=Payment)
def on_payment(sender, instance, **kwargs):
    """A session payment was received — post it once (deduped on the payment)."""
    if instance.status != 'paid':
        return
    user = instance.user
    who = (user.first_name or user.username) if user else 'Someone'
    session = instance.session
    safe_emit(
        ActivityEvent.KIND_PAYMENT,
        f"{who} paid €{instance.amount:.2f} for {session.name}",
        actor=user,
        url=session.get_absolute_url() if instance.session_id else '',
        action_label='View',
        context=session.name if instance.session_id else '',
        target=instance,
        dedup=True,
    )
