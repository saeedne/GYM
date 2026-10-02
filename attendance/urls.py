from django.urls import path
from . import views

app_name = "attendance"
urlpatterns = [
    path("", views.checkin, name="checkin"),
    path("<int:pk>/checkout/", views.checkout, name="checkout"),
    path("reports/", views.report, name="report"),
]
