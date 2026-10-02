from django.urls import path
from . import views

app_name = "finance"
urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("entries/new/", views.entry_create, name="entry_create"),
    path("accounts/", views.account_list, name="accounts"),
    path("accounts/<int:pk>/edit/", views.account_edit, name="account_edit"),
    path("accounts/<int:pk>/delete/", views.account_delete, name="account_delete"),
    path("categories/", views.category_list, name="categories"),
    path("categories/<int:pk>/edit/", views.category_edit, name="category_edit"),
    path("categories/<int:pk>/delete/", views.category_delete, name="category_delete"),
    path("reports/", views.report, name="report"),
]
