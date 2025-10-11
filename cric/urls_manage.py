from django.urls import path
from .views import create_session_view, attendance_view, payments_view, UsersHtmxTableView, edit_user_view, match_attendance_detail_view, create_user_view
from .views_polls import poll_detail_view, create_poll_view

app_name = 'cric'

urlpatterns = [
    path('create-session/', create_session_view, name="manage-create-session"),
    path('attendance/', attendance_view, name='attendance_list'),
    path('attendance/<int:match_id>/', match_attendance_detail_view, name='match_attendance_detail'),
    path('payments/', payments_view, name="manage-payments"),
    path('manage-users/', UsersHtmxTableView.as_view(), name="manage-users"),
    path('edit-user/<int:user_id>/', edit_user_view, name="edit-user"),
    path('users/create/', create_user_view, name="create_user"),
    path('poll/<int:poll_id>/', poll_detail_view, name='poll_detail'),
    path('match/<int:match_id>/create-poll/', create_poll_view, name='create_poll'),
]
