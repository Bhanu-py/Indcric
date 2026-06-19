from django.contrib import admin
from .models import (
    ActivityEvent, ActivityFeedState, BotEvent, OutboundMessage, WhatsAppIdentity,
)


class _MappedFilter(admin.SimpleListFilter):
    title = 'mapped'
    parameter_name = 'mapped'

    def lookups(self, request, model_admin):
        return [('no', 'Unmapped'), ('yes', 'Mapped')]

    def queryset(self, request, qs):
        if self.value() == 'no':
            return qs.filter(user__isnull=True)
        if self.value() == 'yes':
            return qs.filter(user__isnull=False)
        return qs


@admin.register(WhatsAppIdentity)
class WhatsAppIdentityAdmin(admin.ModelAdmin):
    """Map each discovered WhatsApp LID to an IndCric user. Saving sets the
    user's wa_lid, so their group votes start counting. Filter to 'Unmapped',
    match the display name to a member, pick the user, Save."""
    list_display = ('lid', 'name', 'user', 'last_seen')
    list_editable = ('user',)            # assign the user inline from the list
    list_filter = (_MappedFilter,)
    search_fields = ('lid', 'name', 'user__username', 'user__first_name')
    list_per_page = 50


@admin.register(OutboundMessage)
class OutboundMessageAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'status', 'target', 'body', 'attempts', 'sent_at')
    list_filter = ('status', 'target')
    search_fields = ('body', 'dedup_key', 'wa_message_id')
    readonly_fields = ('created_at', 'claimed_at', 'sent_at')


@admin.register(BotEvent)
class BotEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'direction', 'action', 'phone', 'user', 'wa_message_id')
    list_filter = ('direction', 'action')
    search_fields = ('phone', 'wa_message_id', 'user__username')
    readonly_fields = ('created_at', 'wa_message_id', 'phone', 'user', 'action', 'direction', 'payload')


@admin.register(ActivityEvent)
class ActivityEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'kind', 'body', 'actor', 'context')
    list_filter = ('kind',)
    search_fields = ('body', 'context', 'actor__username')
    readonly_fields = ('created_at',)


@admin.register(ActivityFeedState)
class ActivityFeedStateAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_seen_at')
    search_fields = ('user__username',)
