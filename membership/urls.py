from django.urls import path
from . import views

app_name = "membership"
urlpatterns = [
    path("plans/", views.plan_list, name="plans"),
    path("plans/<int:pk>/edit/", views.plan_edit, name="plan_edit"),
    path("plans/<int:pk>/delete/", views.plan_delete, name="plan_delete"),
    path("contracts/", views.contract_list, name="contracts"),
    path("contracts/new/", views.contract_create, name="contract_create"),
    path("contracts/<int:pk>/edit/", views.contract_edit, name="contract_edit"),
    path("contracts/<int:pk>/delete/", views.contract_delete, name="contract_delete"),
    path("contracts/<int:pk>/renew/", views.contract_renew, name="contract_renew"),
    path("payments/", views.payment_list, name="payments"),
    path("payments/new/", views.payment_create, name="payment_create"),
]
