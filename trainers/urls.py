from django.urls import path
from . import views

app_name = "trainers"
urlpatterns = [
    path("", views.trainer_list, name="home"),
    path("trainers/", views.trainer_list, name="list"),
    path("trainers/<int:pk>/edit/", views.trainer_edit, name="trainer_edit"),
    path("trainers/<int:pk>/delete/", views.trainer_delete, name="trainer_delete"),
    path("classes/", views.class_list, name="classes"),
    path("classes/new/", views.class_create, name="class_create"),
    path("classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("classes/<int:pk>/delete/", views.class_delete, name="class_delete"),
    path("classes/<int:pk>/book/", views.class_book, name="book"),
    path("bookings/<int:pk>/cancel/", views.booking_cancel, name="cancel"),
    path("bookings/<int:pk>/attendance/", views.mark_attendance, name="attendance"),
]
