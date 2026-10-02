from django.urls import path
from . import views
app_name="crm"
urlpatterns=[path("",views.leads,name="leads"),path("new/",views.lead_create,name="lead_create"),path("<int:pk>/edit/",views.lead_edit,name="lead_edit"),path("<int:pk>/delete/",views.lead_delete,name="lead_delete"),path("<int:pk>/",views.lead_detail,name="lead_detail"),path("activities/<int:pk>/complete/",views.complete_activity,name="complete_activity"),path("messages/",views.message_queue,name="messages")]
