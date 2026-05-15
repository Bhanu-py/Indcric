from django.urls import path
from . import views

urlpatterns = [
    path('poll/<int:poll_id>/', views.poll_detail_view, name='poll_detail'),
    path('session/<int:session_id>/create-poll/', views.create_poll_view, name='create_poll'),
]
