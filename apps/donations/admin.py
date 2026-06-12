from django.contrib import admin

from .models import Donation, DonationCampaign, DonationSettings, FundItem


@admin.register(DonationSettings)
class DonationSettingsAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'account_holder', 'iban')

    def has_add_permission(self, request):
        # Single-row config: block adding a second once one exists.
        return not DonationSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


class FundItemInline(admin.TabularInline):
    model = FundItem
    extra = 1
    fields = ('order', 'icon', 'color', 'title', 'description')


class DonationInline(admin.TabularInline):
    model = Donation
    extra = 0
    fields = ('user', 'donor_name', 'amount', 'is_anonymous', 'donated_on', 'note')
    autocomplete_fields = ('user',)


@admin.register(DonationCampaign)
class DonationCampaignAdmin(admin.ModelAdmin):
    list_display = ('title', 'goal_amount', 'raised', 'supporter_count', 'is_active', 'created_at')
    list_filter = ('is_active',)
    search_fields = ('title',)
    inlines = [FundItemInline, DonationInline]


@admin.register(Donation)
class DonationAdmin(admin.ModelAdmin):
    list_display = ('display_name', 'amount', 'campaign', 'source', 'donated_on', 'logged_by')
    list_filter = ('source', 'campaign', 'is_anonymous', 'donated_on')
    search_fields = ('donor_name', 'user__username', 'user__first_name', 'note')
    autocomplete_fields = ('user',)
