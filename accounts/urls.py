from django.urls import path
from . import views
app_name = "accounts"
urlpatterns = [
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<int:pk>/", views.user_edit, name="user_edit"),
    path("users/<int:pk>/access/", views.user_access_edit, name="user_access_edit"),
    path("users/<int:pk>/remove/", views.user_membership_delete, name="user_membership_delete"),
    path("roles/", views.role_list, name="role_list"),
    path("roles/new/", views.role_create, name="role_create"),
    path("roles/<int:pk>/", views.role_edit, name="role_edit"),
    path("roles/<int:pk>/delete/", views.role_delete, name="role_delete"),
]
