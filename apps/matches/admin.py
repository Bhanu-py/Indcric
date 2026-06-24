from django.contrib import admin
from .models import Match, Team, Player, Innings, Delivery, Retirement, TemporaryScoringAccess

admin.site.register(Match)
admin.site.register(Team)
admin.site.register(Player)
admin.site.register(Retirement)


@admin.register(Innings)
class InningsAdmin(admin.ModelAdmin):
    list_display = ('match', 'number', 'batting_team', 'bowling_team', 'is_closed')
    list_filter = ('is_closed',)


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = (
        'innings', 'sequence', 'over_number', 'ball_in_over',
        'striker', 'bowler', 'runs_off_bat', 'extra_type', 'extra_runs', 'is_wicket',
    )
    list_filter = ('extra_type', 'is_wicket')
    ordering = ('innings', 'sequence')


@admin.register(TemporaryScoringAccess)
class TemporaryScoringAccessAdmin(admin.ModelAdmin):
    list_display = ('user', 'session', 'granted_by', 'expires_at', 'is_active', 'is_valid_display')
    list_filter = ('is_active', 'session__date', 'granted_at')
    search_fields = ('user__username', 'user__first_name', 'session__name')
    readonly_fields = ('granted_at', 'granted_by')
    
    def get_fieldsets(self, request, obj=None):
        """Show is_valid only when editing existing object."""
        if obj is None:  # Creating new object
            return (
                ('Grant Information', {
                    'fields': ('user', 'session', 'granted_by', 'granted_at')
                }),
                ('Duration', {
                    'fields': ('expires_at', 'is_active')
                }),
                ('Details', {
                    'fields': ('reason',),
                    'classes': ('collapse',)
                }),
            )
        else:  # Editing existing object
            return (
                ('Grant Information', {
                    'fields': ('user', 'session', 'granted_by', 'granted_at')
                }),
                ('Duration', {
                    'fields': ('expires_at', 'is_active')
                }),
                ('Details', {
                    'fields': ('reason', 'is_valid'),
                    'classes': ('collapse',)
                }),
            )

    def is_valid_display(self, obj):
        """Display validity status in the list view."""
        return '✓ Valid' if obj.is_valid else '✗ Expired/Inactive'
    is_valid_display.short_description = 'Status'

    def save_model(self, request, obj, form, change):
        """Auto-populate granted_by with the current user."""
        if not change:  # Creating new object
            obj.granted_by = request.user
        super().save_model(request, obj, form, change)

    actions = ['revoke_access', 'extend_access_one_hour']

    def revoke_access(self, request, queryset):
        """Admin action to revoke access."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} access(es) revoked.')
    revoke_access.short_description = 'Revoke selected access'

    def extend_access_one_hour(self, request, queryset):
        """Admin action to extend access by 1 hour."""
        from django.utils import timezone
        from datetime import timedelta
        updated = 0
        for obj in queryset:
            if obj.is_active:
                obj.expires_at += timedelta(hours=1)
                obj.save(update_fields=['expires_at'])
                updated += 1
        self.message_user(request, f'{updated} access(es) extended by 1 hour.')
    extend_access_one_hour.short_description = 'Extend access by 1 hour'
