from django.urls import path
from . import views

app_name = "cafe"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("menu/new/", views.menu_item_create, name="menu_create"),
    path("menu/<int:pk>/edit/", views.menu_item_edit, name="menu_edit"),
    path("menu/<int:pk>/delete/", views.menu_item_delete, name="menu_delete"),
    path("orders/new/", views.order_create, name="order_create"),
    path("orders/<int:pk>/<str:status>/", views.order_status, name="order_status"),
]
