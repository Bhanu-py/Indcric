from django.urls import path

from . import views

urlpatterns = [
    path('support/', views.support_view, name='support'),
    path('support/link-donors/', views.link_donors_view, name='link-donors'),
    path('support/transactions/<int:txn_id>/confirm/', views.confirm_transaction_view, name='confirm-transaction'),
    path('support/<int:campaign_id>/log/', views.log_donation_view, name='log-donation'),
]
