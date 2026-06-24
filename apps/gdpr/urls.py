from django.urls import path
from . import views

app_name = 'gdpr'

urlpatterns = [
    path('consent/accept/', views.consent_accept_view, name='consent_accept'),
    path('account/delete/', views.delete_account_view, name='delete_account'),
    path('account/delete/confirm/<uidb64>/<token>/', views.delete_account_confirm_view, name='delete_account_confirm'),
    path('privacy-policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms-of-service/', views.terms_of_service_view, name='terms_of_service'),
]
