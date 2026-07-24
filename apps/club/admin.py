from django.contrib import admin

from .models import ClubConsultationResponse


@admin.register(ClubConsultationResponse)
class ClubConsultationResponseAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "email",
        "proceed_choice",
        "membership_preference",
        "volunteering_choice",
        "updated_at",
    )
    list_filter = ("proceed_choice", "membership_preference", "volunteering_choice", "created_at")
    search_fields = ("name", "email", "phone", "connection", "comments")
    readonly_fields = ("created_at", "updated_at")
