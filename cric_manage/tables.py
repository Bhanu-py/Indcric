import django_tables2 as tables
from django.contrib.auth import get_user_model
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.templatetags.static import static
from cric_users.models import Wallet
from django.conf import settings
import os

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
        """Render wallet amount from the associated Wallet model."""
        try:
            wallet = Wallet.objects.filter(user=record).first()
            if wallet:
                return f"€{wallet.amount:.2f}"
            return "€0.00"
        except Exception as e:
            print(f"Error fetching wallet for user {record.id}: {e}")
            return "€0.00"
        
    def render_role(self, value):
        """Render role with appropriate icon using hardcoded paths"""
        if not value:
            return "-"
            
        value_lower = value.lower() if value else ""
        
        # Use absolute URLs to the static files
        bat_icon_url = "/static/icons/bat.png"
        ball_icon_url = "/static/icons/ball.png"
        
        if value_lower == 'batsman':
            role_html = '<div><img src="{}" class="inline-block w-4 h-4 mr-1" alt="Batsman"/></div>'.format(bat_icon_url)
        elif value_lower == 'bowler':
            role_html = '<div><img src="{}" class="inline-block w-4 h-4 mr-1" alt="Bowler"/></div>'.format(ball_icon_url)
        elif value_lower == 'allrounder':
            role_html = '<div><img src="{}" class="inline-block w-4 h-4 mr-1" alt="Batsman"/><img src="{}" class="inline-block w-4 h-4 mr-1" alt="Bowler"/></div>'.format(bat_icon_url, ball_icon_url)
        else:
            role_html = '<div>{}</div>'.format(value)
            
        return mark_safe(role_html)
    
    def render_batting_rating(self, value):
        """Render batting rating with stars"""
        return self._render_rating(value)
        
    def render_bowling_rating(self, value):
        """Render bowling rating with stars"""
        return self._render_rating(value)
        
    def render_fielding_rating(self, value):
        """Render fielding rating with stars"""
        return self._render_rating(value)
        
    def _render_rating(self, value):
        """Helper method to render ratings with stars"""
        if not value:
            return "-"
            
        # Convert value to float to handle decimal numbers
        try:
            value_float = float(value)
        except (ValueError, TypeError):
            return str(value)
            
        # Generate stars representation
        full_stars = int(value_float)  # Number of full stars
        half_star = value_float - full_stars >= 0.5  # Whether to add a half star
        
        stars_html = ""
        
        # Add full stars
        for i in range(full_stars):
            stars_html += '<span class="text-yellow-400">★</span>'
            
        # Add half star if needed
        if half_star:
            stars_html += '<span class="text-yellow-400">★</span>'
            
        # Add empty stars to make total of 5
        empty_stars = 5 - full_stars - (1 if half_star else 0)
        for i in range(empty_stars):
            stars_html += '<span class="text-gray-300">★</span>'
            
        # Add the numeric value without "/5"
        stars_html += f' <span class="text-xs">({value})</span>'
        
        return mark_safe(stars_html)