from django.urls import path
from . import views_users as views
from .views import UsersHtmxTableView, create_session_view, attendance_view, match_attendance_detail_view
from .views import payments_view, manage_users, edit_user_view
from .views import session_detail_view, vote_session_view, close_poll_view, save_teams_view
from .views_polls import poll_detail_view, create_poll_view

urlpatterns = [
    path('', views.home_view, name="home"),
    path('create-session/', create_session_view, name='create_session'),
    path('session/<int:session_id>/', session_detail_view, name='session_detail'),
    path('match/<int:match_id>/', views.match_detail_view, name='match_detail'),
    path('poll/<int:poll_id>/', poll_detail_view, name='poll_detail'),
    path('poll/<int:poll_id>/vote/', vote_session_view, name='vote_session'),
    path('poll/<int:poll_id>/toggle/', close_poll_view, name='close_poll'),
    path('session/<int:session_id>/create-poll/', create_poll_view, name='create_poll'),
    path('session/<int:session_id>/save-teams/', save_teams_view, name='save_teams'),
    path('attendance/', attendance_view, name='attendance_list'),
    path('attendance/match/<int:match_id>/', match_attendance_detail_view, name='match_attendance_detail'),
    path('profile/', views.profile_view, name="profile"),
    path('edit/', views.profile_edit_view, name="profile-edit"),
    path('onboarding/', views.profile_edit_view, name="profile-onboarding"),
    path('settings/', views.profile_settings_view, name="profile-settings"),
    path('emailchange/', views.profile_emailchange, name="profile-emailchange"),
    path('usernamechange/', views.profile_usernamechange, name="profile-usernamechange"),
    path('emailverify/', views.profile_emailverify, name="profile-emailverify"),
    path('delete/', views.profile_delete_view, name="profile-delete"),
    path('payments/', payments_view, name='payments'),
    path('manage-users/', manage_users, name='manage-users'),
    path('users/edit/<int:user_id>/', edit_user_view, name='edit_user'),
    path('users/table/', UsersHtmxTableView.as_view(), name='users_table'),
]
