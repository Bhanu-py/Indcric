from django.urls import path
from . import views

urlpatterns = [
    path('match/<int:match_id>/', views.match_detail_view, name='match_detail'),
]
