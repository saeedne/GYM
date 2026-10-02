from django.urls import path
from . import views

app_name = "workouts"
urlpatterns = [
    path("", views.plans, name="plans"),
    path("plans/<int:pk>/", views.plan_detail, name="plan_detail"),
    path("plans/<int:pk>/edit/", views.plan_edit, name="plan_edit"),
    path("plans/<int:pk>/delete/", views.workout_plan_delete, name="plan_delete"),
    path("exercises/", views.exercise_library, name="exercises"),
    path("exercises/<int:pk>/edit/", views.exercise_edit, name="exercise_edit"),
    path("exercises/<int:pk>/delete/", views.exercise_delete, name="exercise_delete"),
    path("assignments/", views.assignments, name="assignments"),
    path("assessments/", views.assessments, name="assessments"),
]
