"""URL patterns for reports app."""

from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('tax-compliance/', views.tax_report_download, name='tax_report_download'),
]
