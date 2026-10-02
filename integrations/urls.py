from django.urls import path
from . import views
app_name="integrations"
urlpatterns=[path("",views.member_portal,name="member_portal"),path("v1/summary/",views.api_summary,name="api_summary"),path("v1/members/",views.api_members,name="api_members")]
