from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('create-session/', views.create_session_view, name='create_session'),
    path('session/<int:session_id>/', views.session_detail_view, name='session_detail'),
    path('session/<int:session_id>/delete/', views.delete_session_view, name='delete_session'),
    path('session/<int:session_id>/save-teams/', views.save_teams_view, name='save_teams'),
    path('session/<int:session_id>/add-match/', views.add_match_view, name='add_match'),
    path('match/<int:match_id>/record-score/', views.record_score_view, name='record_score'),
    path('match/<int:match_id>/delete/', views.delete_match_view, name='delete_match'),
    path('poll/<int:poll_id>/vote/', views.vote_session_view, name='vote_session'),
    path('poll/<int:poll_id>/toggle/', views.close_poll_view, name='close_poll'),
    path('manage/attendance/', views.attendance_view, name='attendance_list'),
    path('manage/attendance/<int:match_id>/', views.match_attendance_detail_view, name='match_attendance_detail'),
    path('manage/payments/', views.payments_view, name='manage-payments'),
]
