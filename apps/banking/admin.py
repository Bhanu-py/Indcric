from django.contrib import admin

from .models import BankLink, BankTransaction


@admin.register(BankLink)
class BankLinkAdmin(admin.ModelAdmin):
    list_display = ('label', 'provider', 'iban', 'is_active', 'consent_valid_until', 'last_synced_at')
    list_filter = ('provider', 'is_active')
    search_fields = ('label', 'iban', 'institution_id')


@admin.register(BankTransaction)
class BankTransactionAdmin(admin.ModelAdmin):
    list_display = ('booked_on', 'counterparty_name', 'amount', 'currency', 'status', 'donation')
    list_filter = ('status', 'currency', 'link')
    search_fields = ('counterparty_name', 'counterparty_iban', 'remittance', 'transaction_id')
    date_hierarchy = 'booked_on'
    readonly_fields = ('transaction_id', 'raw', 'imported_at')
