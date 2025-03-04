from decimal import Decimal
from django.db.models import Q
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

