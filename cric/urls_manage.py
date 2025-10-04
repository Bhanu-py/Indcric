from django.urls import path
from .views import create_match_view, attendance_view, payments_view, UsersHtmxTableView, edit_user_view
from .views_enhanced import enhanced_attendance_view, export_period_excel, ajax_update_attendance

urlpatterns = [
    path('create-match/', create_match_view, name="manage-create-match"),
    path('attendance/', attendance_view, name="manage-attendance"),
    path('enhanced-attendance/', enhanced_attendance_view,
         name="enhanced_attendance"),
    path('export-period/<int:period_id>/',
         export_period_excel, name="export_period_excel"),
    path('ajax/update-attendance/', ajax_update_attendance,
         name="ajax_update_attendance"),
    path('payments/', payments_view, name="manage-payments"),
    path('manage-users/', UsersHtmxTableView.as_view(), name="manage-users"),
    path('edit-user/<int:user_id>/', edit_user_view, name="edit-user"),
]
