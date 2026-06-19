from django.urls import path
from . import views

urlpatterns = [
    path('api/bot/whatsapp/', views.whatsapp_webhook, name='bot_whatsapp'),
    path('api/bot/run-reminders/', views.run_reminders_view, name='bot_run_reminders'),

    path('activity/', views.activity_feed_view, name='activity'),
    path('activity/read-all/', views.activity_read_all_view, name='activity_read_all'),
]
