from django.contrib import admin
from .models import User, Session, Match, Team, Attendance, Payment, SessionPlayer, Poll, Vote, BotEvent


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_staff')
    search_fields = ('username', 'email', 'phone')


@admin.register(BotEvent)
class BotEventAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'direction', 'action', 'phone', 'user', 'wa_message_id')
    list_filter = ('direction', 'action')
    search_fields = ('phone', 'wa_message_id', 'user__username')
    readonly_fields = ('created_at', 'wa_message_id', 'phone', 'user', 'action', 'direction', 'payload')


admin.site.register(Session)
admin.site.register(Match)
admin.site.register(Team)
admin.site.register(Attendance)
admin.site.register(Payment)
admin.site.register(SessionPlayer)
admin.site.register(Poll)
admin.site.register(Vote)
