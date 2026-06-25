from django.contrib import admin
from .models import User, PlayerProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'wa_lid', 'role', 'is_staff')
    search_fields = ('username', 'email', 'phone', 'wa_lid')
    # Surface the avatar so staff can moderate/remove a member's picture.
    fields = ('username', 'first_name', 'last_name', 'email', 'phone', 'wa_lid', 'avatar',
              'role', 'batting_rating', 'bowling_rating', 'fielding_rating',
              'is_active', 'is_staff', 'is_superuser')


admin.site.register(PlayerProfile)
