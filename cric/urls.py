from django.urls import path
from . import views
from . import views_users
from .views import UsersHtmxTableView, create_session_view, attendance_view, match_attendance_detail_view
from .views import payments_view, manage_users, edit_user_view, create_user_view, delete_session_view, delete_user_view
from .views import session_detail_view, vote_session_view, close_poll_view, save_teams_view, delete_session_view
from .views_polls import poll_detail_view, create_poll_view

urlpatterns = [
    path('', views.home, name='home'),
    path('create-session/', create_session_view, name='create_session'),
    path('session/<int:session_id>/', session_detail_view, name='session_detail'),
    path('session/<int:session_id>/delete/', delete_session_view, name='delete_session'),
    path('poll/<int:poll_id>/', poll_detail_view, name='poll_detail'),
    path('poll/<int:poll_id>/vote/', vote_session_view, name='vote_session'),
    path('poll/<int:poll_id>/toggle/', close_poll_view, name='close_poll'),
    path('session/<int:session_id>/create-poll/', create_poll_view, name='create_poll'),
    path('session/<int:session_id>/save-teams/', save_teams_view, name='save_teams'),
    path('attendance/', attendance_view, name='attendance_list'),
    path('attendance/match/<int:match_id>/', match_attendance_detail_view, name='match_attendance_detail'),
    path('payments/', payments_view, name='payments'),
    
    # User management URLs
    path('manage-users/', manage_users, name='manage-users'),
    path('users/edit/<int:user_id>/', edit_user_view, name='edit_user'),
    path('users/create/', create_user_view, name='create_user'),
    path('users/delete/<int:user_id>/', delete_user_view, name='delete_user'),
    path('users/table/', UsersHtmxTableView.as_view(), name='users_table'),
    
    # Profile URLs
    path('profile/', views_users.profile_view, name='profile'),
    path('profile/<str:username>/', views_users.profile_view, name='profile_with_username'),
    path('profile/edit/', views_users.profile_edit_view, name='profile_edit'),
    path('profile/settings/', views_users.profile_settings_view, name='profile-settings'),
    path('profile/email/', views_users.profile_emailchange, name='profile-email-change'),
    path('profile/username/', views_users.profile_usernamechange, name='profile-username-change'),
    path('profile/verify-email/', views_users.profile_emailverify, name='profile-email-verify'),
    path('profile/delete/', views_users.profile_delete_view, name='profile-delete'),
    path('profile/onboarding/', views_users.profile_onboarding_view, name='profile-onboarding'),
]
