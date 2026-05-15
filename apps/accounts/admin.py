from django.contrib import admin
from .models import User, PlayerProfile


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'phone', 'role', 'is_staff')
    search_fields = ('username', 'email', 'phone')


admin.site.register(PlayerProfile)
