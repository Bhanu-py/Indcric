import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.db.models import Sum
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
        # Wallet is a transaction ledger — balance is the sum of all rows.
        balance = (
            Wallet.objects.filter(user=record).aggregate(s=Sum('amount'))['s']
            or 0
        )
        return f"€{balance:.2f}"

    # SVG glyphs from design_handoff/preview/icons.html — bat (sky),
    # ball (red), allrounder (purple). Rendered as an icon-only chip
    # so the role column reads at a glance without redundant labels.
    _ROLE_ICONS = {
        'batsman': (
            'Batsman', 'bg-sky-100 text-sky-700',
            '<path d="M12 3v5"/><path d="M10 5.5h4"/>'
            '<rect x="9" y="8.5" width="6" height="12.5" rx="1.5"/>'
        ),
        'bowler': (
            'Bowler', 'bg-red-50 text-red-700',
            '<circle cx="12" cy="12" r="8.5"/>'
            '<path d="M5 14c3.5 2.5 10.5 2.5 14 0"/>'
            '<path d="M8 14.6v1.4M11 15.4v1.4M14 15.4v1.4M16.8 14.6v1.4"/>'
        ),
        'allrounder': (
            'All-Rounder', 'bg-purple-100 text-purple-700',
            '<path d="M4 4l4 4"/><path d="M7 7l9 9"/>'
            '<path d="M14 14l3 3"/><circle cx="6.5" cy="17.5" r="3"/>'
        ),
    }

    def render_role(self, value):
        if not value:
            return mark_safe('<span class="text-stone-300">—</span>')
        role = self._ROLE_ICONS.get(value.lower())
        if role is None:
            return value
        label, classes, paths = role
        return mark_safe(
            f'<span title="{label}" class="inline-flex items-center justify-center '
            f'w-8 h-8 rounded-lg {classes}">'
            f'<svg class="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
            f'stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round">'
            f'{paths}</svg></span>'
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
