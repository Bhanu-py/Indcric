from django.urls import path
from . import views

urlpatterns = [
    path('', views.home_view, name="home"),
    path('match/<int:match_id>/', views.match_detail_view, name='match_detail'),
    path('profile/', views.profile_view, name="profile"),
    path('edit/', views.profile_edit_view, name="profile-edit"),
    path('onboarding/', views.profile_edit_view, name="profile-onboarding"),
    path('settings/', views.profile_settings_view, name="profile-settings"),
    path('emailchange/', views.profile_emailchange, name="profile-emailchange"),
    path('usernamechange/', views.profile_usernamechange, name="profile-usernamechange"),
    path('emailverify/', views.profile_emailverify, name="profile-emailverify"),
    path('delete/', views.profile_delete_view, name="profile-delete"),
]
