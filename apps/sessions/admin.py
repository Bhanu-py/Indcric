from django.contrib import admin
from .models import Session, SessionPlayer, Attendance

admin.site.register(Session)
admin.site.register(SessionPlayer)
admin.site.register(Attendance)
