from django.urls import path

from . import views

urlpatterns = [
    path('jerseys/', views.jersey_orders_view, name='jersey-orders'),
    path('jerseys/admin/', views.jersey_orders_admin_view, name='jersey-orders-admin'),
    path('jerseys/export/', views.export_jersey_orders_view, name='jersey-orders-export'),
    path('jerseys/<int:order_id>/edit/', views.edit_jersey_order_view, name='jersey-order-edit'),
    path('jerseys/<int:order_id>/delete/', views.delete_jersey_order_view, name='jersey-order-delete'),
]
