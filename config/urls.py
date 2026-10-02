from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import include, path
from accounts.views import GymLoginView
from integrations.views import service_worker
from core.appearance import appearance_settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("core.urls")),
    path("members/", include("members.urls")),
    path("membership/", include("membership.urls")),
    path("attendance/", include("attendance.urls")),
    path("access/", include("access_control.urls")),
    path("training/", include("trainers.urls")),
    path("store/", include("store.urls")),
    path("cafe/", include("cafe.urls")),
    path("fitness/", include("workouts.urls")),
    path("finance/", include("finance.urls")),
    path("crm/", include("crm.urls")),
    path("reports/", include("reports.urls")),
    path("api/", include("integrations.urls")),
    path("accounts/", include("accounts.urls")),
    path("mobile/", include("integrations.mobile_urls")),
    path("service-worker.js", service_worker, name="service_worker"),
    path("equipment/", include("equipment.urls")),
    path("settings/appearance/", appearance_settings, name="appearance_settings"),
    path(
        "login/",
        GymLoginView.as_view(),
        name="login",
    ),
    path("logout/", LogoutView.as_view(), name="logout"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
