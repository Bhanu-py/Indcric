from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from apps.matches.models import TemporaryScoringAccess
from django.utils import timezone


@login_required
def debug_scoring_access(request):
    """Debug view to check scoring access for current user."""
    all_access = TemporaryScoringAccess.objects.all()
    user_access = TemporaryScoringAccess.objects.filter(user=request.user)
    
    context = {
        'current_user': request.user,
        'all_access': all_access,
        'user_access': user_access,
        'current_time': timezone.now(),
    }
    
    return render(request, 'debug/scoring_access_debug.html', context)
