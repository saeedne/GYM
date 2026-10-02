from django.urls import path
from . import views
app_name="equipment"
urlpatterns=[path("",views.list_equipment,name="list"),path("new/",views.create_equipment,name="create"),path("<int:pk>/edit/",views.edit_equipment,name="edit"),path("<int:pk>/delete/",views.equipment_delete,name="delete"),path("<int:pk>/maintenance/",views.add_maintenance,name="maintenance")]
