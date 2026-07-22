from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("donate/", views.donate, name="donate"),
    path("contact/", views.contact, name="contact"),
    path("language/", views.set_language, name="set_language"),
]
