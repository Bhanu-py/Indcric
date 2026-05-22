from django.urls import path
from . import views

urlpatterns = [
    path('api/bot/whatsapp/', views.whatsapp_webhook, name='bot_whatsapp'),
    path('api/bot/rsvp/', views.bot_rsvp_view, name='bot_rsvp'),
    path('api/bot/run-reminders/', views.run_reminders_view, name='bot_run_reminders'),
]
