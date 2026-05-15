from django.contrib import admin
from .models import BotEvent


@admin.register(BotEvent)
class BotEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'direction', 'action', 'phone', 'user', 'wa_message_id')
    list_filter = ('direction', 'action')
    search_fields = ('phone', 'wa_message_id', 'user__username')
    readonly_fields = ('created_at', 'wa_message_id', 'phone', 'user', 'action', 'direction', 'payload')
