import os, django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'cric_core.settings')
django.setup()

from cric.models import Poll, Vote, User

poll = Poll.objects.latest('id')
users = User.objects.all()
created = 0
for u in users:
    _, made = Vote.objects.get_or_create(poll=poll, user=u, defaults={'choice': 'yes'})
    if made:
        created += 1

yes_count = poll.votes.filter(choice='yes').count()
print(f"Poll: {poll.session.name}")
print(f"New votes added: {created}")
print(f"Total yes votes: {yes_count}")
