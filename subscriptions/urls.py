from django.urls import path

from . import views

app_name = "subscriptions"

urlpatterns = [
    path("", views.plans, name="plans"),
    path("join/<slug:slug>/", views.join, name="join"),
    path("payment-success/", views.payment_success, name="payment_success"),
    path("payment-failed/", views.payment_failed, name="payment_failed"),
    path("razorpay/webhook/", views.razorpay_webhook, name="razorpay_webhook"),
    path("invoice/<int:pk>/", views.invoice_detail, name="invoice"),
    path("invoice/<int:pk>/download/", views.invoice_download, name="invoice_download"),
    path("certificate/<int:pk>/", views.certificate_detail, name="certificate"),
    path("certificate/<int:pk>/download/", views.certificate_download, name="certificate_download"),
]
