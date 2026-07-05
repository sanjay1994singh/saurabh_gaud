"""
URL configuration for dharm_raksha_sangh project.
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("social_django.urls", namespace="social")),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("events/", include("events.urls")),
    path("hamare-stambh/", include("hamare_stambh.urls")),
    path("seva-prakalp/", include("seva_prakalp.urls")),
    path("subscriptions/", include("subscriptions.urls")),
    path("", include("home.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
