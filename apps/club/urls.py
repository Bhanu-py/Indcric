from django.urls import path

from . import views

app_name = "club"

urlpatterns = [
    path("cricket-club/admin/", views.cricket_club_admin_view, name="cricket-club-admin"),
    path("cricket-club/", views.cricket_club_view, name="cricket-club"),
]
