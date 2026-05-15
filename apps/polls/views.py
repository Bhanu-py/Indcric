from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden

from .models import Poll, Vote
from .forms import PollForm


@login_required
def poll_detail_view(request, poll_id):
    poll = get_object_or_404(Poll, id=poll_id)
    user_vote = None
    if request.user.is_authenticated:
        vote = Vote.objects.filter(poll=poll, user=request.user).first()
        if vote:
            user_vote = vote.choice

    if request.method == 'POST':
        if not poll.is_open:
            return HttpResponseForbidden("This poll is closed.")
        choice = request.POST.get('choice')
        if choice in ['yes', 'no']:
            Vote.objects.update_or_create(
                poll=poll, user=request.user, defaults={'choice': choice}
            )
        return redirect('poll_detail', poll_id=poll.id)

    yes_votes = poll.votes.filter(choice='yes').count()
    no_votes = poll.votes.filter(choice='no').count()
    total_votes = yes_votes + no_votes

    context = {
        'poll': poll,
        'yes_votes': yes_votes,
        'no_votes': no_votes,
        'total_votes': total_votes,
        'user_vote': user_vote,
        'poll_url': request.build_absolute_uri(poll.get_absolute_url()),
    }
    return render(request, 'cric/pages/poll_detail.html', context)


@login_required
def create_poll_view(request, session_id):
    from apps.sessions.models import Session
    session = get_object_or_404(Session, id=session_id)
    if hasattr(session, 'poll'):
        return redirect('poll_detail', poll_id=session.poll.id)

    if request.method == 'POST':
        form = PollForm(request.POST)
        if form.is_valid():
            poll = form.save(commit=False)
            poll.session = session
            poll.save()
            from apps.notifications.services import notify_poll_created
            notify_poll_created(poll)
            return redirect('poll_detail', poll_id=poll.id)
    else:
        form = PollForm()

    return render(request, 'cric/pages/create_poll.html', {'form': form, 'session': session})
