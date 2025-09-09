from django.contrib import admin
from django.urls import include, path
from django.conf.urls.static import static
from config import settings
from apps.passports.views import RegistryDashboardView
from web_project.views import SystemView

admin.site.site_header = 'Реестр паспортов'
admin.site.site_title = 'Реестр паспортов'

urlpatterns = [
    path("admin/", admin.site.urls),

    path("auth/", include(("apps.authentication.urls", "auth"), namespace="auth")),

    path("dashboard/", RegistryDashboardView.as_view(), name="dashboard"),

    path("", include("apps.pages.urls")),

    path("", include("apps.passports.urls", namespace="passports")),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = SystemView.as_view(template_name="pages_misc_error.html", status=404)
handler400 = SystemView.as_view(template_name="pages_misc_error.html", status=400)
handler500 = SystemView.as_view(template_name="pages_misc_error.html", status=500)
