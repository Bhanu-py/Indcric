import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.utils.safestring import mark_safe

from apps.payments.models import Wallet

User = get_user_model()


class UserHTMxTable(tables.Table):
    id = tables.Column(verbose_name="ID")
    username = tables.Column(verbose_name="Username")
    role = tables.Column(verbose_name="Role")
    batting_rating = tables.Column(verbose_name="Batting")
    bowling_rating = tables.Column(verbose_name="Bowling")
    fielding_rating = tables.Column(verbose_name="Fielding")
    is_staff = tables.BooleanColumn(verbose_name="Staff Status", yesno='✓,✗')
    last_login = tables.Column(verbose_name="Last Login")
    wallet_amount = tables.Column(verbose_name="Wallet Amount", empty_values=(), orderable=False)

    class Meta:
        model = User
        template_name = "tables/tailwind_table.html"
        fields = ("id", "username", "role", "batting_rating", "bowling_rating", "fielding_rating", "is_staff", "last_login", "wallet_amount")
        sequence = ("id", "username", "role", "batting_rating", "bowling_rating", "fielding_rating", "last_login", "is_staff", "wallet_amount")

    def render_wallet_amount(self, record):
        try:
            wallet = Wallet.objects.filter(user=record).first()
            if wallet:
                return f"€{wallet.amount:.2f}"
            return "€0.00"
        except Exception:
            return "€0.00"

    def render_role(self, value):
        if not value:
            return "-"
        value_lower = value.lower()
        badges = {
            'batsman':    ('🏏', 'Batsman',    'bg-sky-100 text-sky-800'),
            'bowler':     ('🎯', 'Bowler',     'bg-red-100 text-red-800'),
            'allrounder': ('⭐', 'All-Rounder', 'bg-purple-100 text-purple-800'),
        }
        icon, label, classes = badges.get(value_lower, ('', value, 'bg-stone-100 text-stone-700'))
        return mark_safe(
            f'<span class="inline-flex items-center gap-1 px-2 py-0.5 rounded-full '
            f'text-xs font-medium {classes}">{icon} {label}</span>'
        )

    def render_batting_rating(self, value):
        return self._render_rating(value)

    def render_bowling_rating(self, value):
        return self._render_rating(value)

    def render_fielding_rating(self, value):
        return self._render_rating(value)

    def _render_rating(self, value):
        if not value:
            return "-"
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            return str(value)

        full_stars = int(value_float)
        half_star = value_float - full_stars >= 0.5
        stars_html = ""
        for _ in range(full_stars):
            stars_html += '<span class="text-yellow-400">★</span>'
        if half_star:
            stars_html += '<span class="text-yellow-400">★</span>'
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        for _ in range(empty_stars):
            stars_html += '<span class="text-gray-300">★</span>'
        stars_html += f' <span class="text-xs">({value})</span>'
        return mark_safe(stars_html)
