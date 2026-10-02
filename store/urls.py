from django.urls import path
from . import views

app_name = "store"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("products/new/", views.product_create, name="product_create"),
    path("products/<int:pk>/edit/", views.product_edit, name="product_edit"),
    path("products/<int:pk>/delete/", views.product_delete, name="product_delete"),
    path("stock/", views.stock_adjust, name="stock"),
    path("sell/", views.sell, name="sell"),
    path("sales/", views.sales, name="sales"),
]
