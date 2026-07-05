from django.contrib import admin

from .models import Certificate, MembershipSubscription, SubscriptionPlan


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "member_type_text",
        "plan_type",
        "amount",
        "duration_days",
        "is_active",
        "display_order",
    )
    list_filter = ("plan_type", "is_active")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name", "member_type_text", "description")


@admin.register(MembershipSubscription)
class MembershipSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "status", "starts_at", "ends_at", "created_at")
    list_filter = ("status", "plan", "created_at")
    search_fields = ("user__username", "user__email", "razorpay_order_id", "razorpay_payment_id")
    readonly_fields = (
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "created_at",
        "updated_at",
    )


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "user", "subscription", "issued_at")
    search_fields = ("certificate_number", "user__username", "user__email")
    readonly_fields = ("certificate_number", "issued_at")
