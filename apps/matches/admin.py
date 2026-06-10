from django.contrib import admin
from .models import Match, Team, Player, Innings, Delivery, Retirement

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
