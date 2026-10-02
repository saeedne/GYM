from django.urls import path
from . import views

app_name = "access_control"
urlpatterns = [
    path("credentials/", views.credentials, name="credentials"),
    path("credentials/<int:pk>/toggle/", views.credential_toggle, name="credential_toggle"),
    path("policy/", views.policy, name="policy"),
    path("guests/", views.guests, name="guests"),
    path("guests/<int:pk>/checkin/", views.guest_checkin, name="guest_checkin"),
]
