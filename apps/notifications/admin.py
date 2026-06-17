from django.contrib import admin
from .models import ActivityEvent, ActivityFeedState, BotEvent, Reaction


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


@admin.register(Reaction)
class ReactionAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'activity', 'user', 'emoji')
    search_fields = ('user__username', 'emoji')


@admin.register(ActivityFeedState)
class ActivityFeedStateAdmin(admin.ModelAdmin):
    list_display = ('user', 'last_seen_at')
    search_fields = ('user__username',)
