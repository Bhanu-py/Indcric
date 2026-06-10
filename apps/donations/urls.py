from django.urls import path

from . import views

urlpatterns = [
    path('support/', views.support_view, name='support'),
    path('support/<int:campaign_id>/log/', views.log_donation_view, name='log-donation'),
]
