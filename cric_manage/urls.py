from django.urls import path
from .views import create_match_view, attendance_view, payments_view, UsersHtmxTableView

urlpatterns = [
    path('create-match/', create_match_view, name="manage-create-match"),
    path('attendance/', attendance_view, name="manage-attendance"),
    path('payments/', payments_view, name="manage-payments"),
    path('manage-users/', UsersHtmxTableView.as_view(), name="manage-users"),
]
