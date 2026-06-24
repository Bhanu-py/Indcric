from django.urls import path
from . import views, views_bot

urlpatterns = [
    path('api/bot/whatsapp/', views.whatsapp_webhook, name='bot_whatsapp'),
    path('api/bot/run-reminders/', views.run_reminders_view, name='bot_run_reminders'),
    path('api/bot/inbound/', views_bot.inbound_message, name='bot_inbound'),

    path('activity/', views.activity_feed_view, name='activity'),
    path('activity/read-all/', views.activity_read_all_view, name='activity_read_all'),
]
