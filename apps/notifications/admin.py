from django.contrib import admin
from .models import ActivityEvent, ActivityFeedState, BotEvent, OutboundMessage


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
