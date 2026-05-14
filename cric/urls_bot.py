from django.urls import path
from .views_bot import bot_rsvp_view, whatsapp_webhook

urlpatterns = [
    path('whatsapp/', whatsapp_webhook, name='bot_whatsapp'),
    path('rsvp/', bot_rsvp_view, name='bot_rsvp'),
]
