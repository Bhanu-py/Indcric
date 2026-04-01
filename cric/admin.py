from django.contrib import admin
from .models import User, Session, Match, Team, Attendance, Payment, SessionPlayer, Poll, Vote

admin.site.register(User)
admin.site.register(Session)
admin.site.register(Match)
admin.site.register(Team)
admin.site.register(Attendance)
admin.site.register(Payment)
admin.site.register(SessionPlayer)
admin.site.register(Poll)
admin.site.register(Vote)
