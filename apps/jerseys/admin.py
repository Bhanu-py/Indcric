from django.contrib import admin

from .models import JerseyOrder


@admin.register(JerseyOrder)
class JerseyOrderAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'for_person',
        'gender',
        'wearer_name',
        'item_type',
        'size',
        'quantity',
        'jersey_number',
        'line_total',
    )
    list_filter = ('item_type', 'size', 'for_person', 'gender')
    search_fields = ('user__username', 'user__first_name', 'wearer_name', 'jersey_number')
