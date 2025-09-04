from decimal import Decimal
from django.db.models import Q, OuterRef, Subquery, DecimalField, Value
from django.db.models.functions import Coalesce
import django_filters
from cric_users.models import User, Match, Team, Payment, Attendance, Wallet

class UserFilter(django_filters.FilterSet):
    query = django_filters.CharFilter(method='filter_query', label='Search')
    
    role = django_filters.ChoiceFilter(
        choices=[
            ('', 'All Roles'),
            ('batsman', 'Batsman'),
            ('bowler', 'Bowler'),
            ('allrounder', 'All-Rounder')
        ],
        empty_label='All Roles'
    )
    
    # Rating range filters
    min_batting = django_filters.NumberFilter(field_name='batting_rating', lookup_expr='gte', label='Min Batting Rating')
    max_batting = django_filters.NumberFilter(field_name='batting_rating', lookup_expr='lte', label='Max Batting Rating')
    
    min_bowling = django_filters.NumberFilter(field_name='bowling_rating', lookup_expr='gte', label='Min Bowling Rating')
    max_bowling = django_filters.NumberFilter(field_name='bowling_rating', lookup_expr='lte', label='Max Bowling Rating')
    
    min_fielding = django_filters.NumberFilter(field_name='fielding_rating', lookup_expr='gte', label='Min Fielding Rating')
    max_fielding = django_filters.NumberFilter(field_name='fielding_rating', lookup_expr='lte', label='Max Fielding Rating')
    
    # Wallet amount range filters
    min_wallet = django_filters.NumberFilter(method='filter_min_wallet', label='Min Wallet Amount')
    max_wallet = django_filters.NumberFilter(method='filter_max_wallet', label='Max Wallet Amount')
    
    # Sort by wallet field - make this more explicit
    sort_by_wallet = django_filters.ChoiceFilter(
        choices=[
            ('', 'Default'),
            ('asc', 'Wallet (Low to High)'),
            ('desc', 'Wallet (High to Low)')
        ],
        method='filter_sort_by_wallet',
        label='Sort by Wallet',
        empty_label=None  # Remove empty label to ensure the default option is shown
    )
    
    class Meta:
        model = User
        fields = ['query', 'role', 'is_staff']
    
    def filter_query(self, queryset, name, value):
        return queryset.filter(
            Q(username__icontains=value) | 
            Q(email__icontains=value) |
            Q(first_name__icontains=value) |
            Q(last_name__icontains=value)
        )
    
    def _annotate_with_wallet(self, queryset):
        """Helper method to annotate queryset with wallet amount"""
        wallet_subquery = Wallet.objects.filter(
            user=OuterRef('pk')
        ).values('amount')[:1]
        
        return queryset.annotate(
            wallet_value=Coalesce(Subquery(wallet_subquery), Value(0), output_field=DecimalField())
        )
    
    def filter_min_wallet(self, queryset, name, value):
        """Filter users with wallet amount greater than or equal to specified value"""
        queryset = self._annotate_with_wallet(queryset)
        return queryset.filter(wallet_value__gte=value)
    
    def filter_max_wallet(self, queryset, name, value):
        """Filter users with wallet amount less than or equal to specified value"""
        queryset = self._annotate_with_wallet(queryset)
        return queryset.filter(wallet_value__lte=value)
    
    def filter_sort_by_wallet(self, queryset, name, value):
        """Sort users by wallet amount"""
        if not value:
            return queryset
            
        # Print debug info
        print(f"Sorting by wallet: {value}")
        
        queryset = self._annotate_with_wallet(queryset)
        direction = '-' if value == 'desc' else ''
        return queryset.order_by(f'{direction}wallet_value')

