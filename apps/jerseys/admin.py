from django.contrib import admin

from .models import JerseyOrder, JerseyOrderWindow


@admin.register(JerseyOrder)
class JerseyOrderAdmin(admin.ModelAdmin):
    list_display = (
        'user',
        'for_person',
        'gender',
        'wearer_name',
        'item_type',
        'display_size',
        'quantity',
        'jersey_number',
        'line_total',
    )
    list_filter = ('item_type', 'size', 'for_person', 'gender')
    search_fields = ('user__username', 'user__first_name', 'wearer_name', 'jersey_number')


@admin.register(JerseyOrderWindow)
class JerseyOrderWindowAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_enabled', 'opens_at', 'closes_at', 'updated_at')
    fields = ('name', 'is_enabled', 'opens_at', 'closes_at')

    def has_add_permission(self, request):
        if JerseyOrderWindow.objects.exists():
            return False
        return super().has_add_permission(request)
