from django.urls import path
from . import views
app_name="mobile"
urlpatterns=[path("",views.mobile_dashboard,name="dashboard"),path("offline/",views.offline_page,name="offline")]
