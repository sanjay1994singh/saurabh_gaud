"""
URL configuration for dharm_raksha_sangh project.
"""

from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth.views import LoginView
from django.urls import include, path

from accounts.forms import LoginForm

urlpatterns = [
    path("admin/", admin.site.urls),
    path("auth/", include("social_django.urls", namespace="social")),
    path("accounts/login/", LoginView.as_view(authentication_form=LoginForm, template_name="registration/login.html"), name="login"),
    path("accounts/", include("accounts.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
    path("events/", include("events.urls")),
    path("hamare-stambh/", include("hamare_stambh.urls")),
    path("patrika/", include("patrika.urls")),
    path("seva-prakalp/", include("seva_prakalp.urls")),
    path("subscriptions/", include("subscriptions.urls")),
    path("", include("home.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
