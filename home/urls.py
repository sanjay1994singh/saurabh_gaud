from django.urls import path

from . import views

app_name = "home"

urlpatterns = [
    path("", views.index, name="index"),
    path("about/", views.about, name="about"),
    path("donate/", views.donate, name="donate"),
    path("contact/", views.contact, name="contact"),
    path("terms-and-conditions/", views.terms, name="terms"),
    path("privacy-policy/", views.privacy, name="privacy"),
    path("cancellation-and-refunds/", views.refunds, name="refunds"),
    path("shipping-and-delivery/", views.shipping, name="shipping"),
]
