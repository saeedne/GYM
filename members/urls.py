from django.urls import path
from .views import member_create, member_delete, member_detail, member_edit, member_list

urlpatterns = [
    path("", member_list, name="member_list"),
    path("new/", member_create, name="member_create"),
    path("<int:pk>/", member_detail, name="member_detail"),
    path("<int:pk>/edit/", member_edit, name="member_edit"),
    path("<int:pk>/delete/", member_delete, name="member_delete"),
]
