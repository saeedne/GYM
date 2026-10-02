from django.urls import path
from .views import dashboard, switch_club
from .management_views import branch_delete, branch_form, club_delete, club_form, club_management

urlpatterns = [
    path("", dashboard, name="dashboard"),
    path("switch-club/", switch_club, name="switch_club"),
    path("manage/clubs/", club_management, name="club_management"),
    path("manage/clubs/new/", club_form, name="club_create"),
    path("manage/clubs/<int:pk>/edit/", club_form, name="club_edit"),
    path("manage/clubs/<int:pk>/delete/", club_delete, name="club_delete"),
    path("manage/clubs/<int:club_pk>/branches/new/", branch_form, name="branch_create"),
    path("manage/clubs/<int:club_pk>/branches/<int:pk>/edit/", branch_form, name="branch_edit"),
    path("manage/clubs/<int:club_pk>/branches/<int:pk>/delete/", branch_delete, name="branch_delete"),
]
