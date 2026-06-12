from django.urls import path

from . import views

urlpatterns = [
    path('banking/link/', views.link_index, name='banking_link_index'),
    path('banking/link/start/', views.link_start, name='banking_link_start'),
    path('banking/link/callback/', views.link_callback, name='banking_link_callback'),
]
