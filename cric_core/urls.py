from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include('apps.sessions.urls')),
    path('', include('apps.polls.urls')),
    path('', include('apps.matches.urls')),
    path('', include('apps.payments.urls')),
    path('', include('apps.accounts.urls')),
    path('', include('apps.notifications.urls')),
    path("accounts/", include("allauth.urls")),
]
