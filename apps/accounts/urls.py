from django.urls import path
from . import views

urlpatterns = [
    # Profile
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.profile_edit_view, name='profile_edit'),
    path('profile/settings/', views.profile_settings_view, name='profile-settings'),
    path('profile/email/', views.profile_emailchange, name='profile-emailchange'),
    path('profile/username/', views.profile_usernamechange, name='profile-usernamechange'),
    path('profile/verify-email/', views.profile_emailverify, name='profile-email-verify'),
    path('profile/phone/', views.profile_phonechange, name='profile-phonechange'),
    path('profile/delete/', views.profile_delete_view, name='profile-delete'),
    path('profile/onboarding/', views.profile_onboarding_view, name='profile-onboarding'),
    path('profile/<str:username>/', views.profile_view, name='profile_with_username'),

    # User management (staff)
    path('manage/manage-users/', views.UsersHtmxTableView.as_view(), name='manage-users'),
    path('manage/users/create/', views.create_user_view, name='create_user'),
    path('manage/users/edit/<int:user_id>/', views.edit_user_view, name='edit-user'),
    path('manage/users/delete/<int:user_id>/', views.delete_user_view, name='delete_user'),
]
