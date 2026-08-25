from django.contrib import admin

from .models import Certificate, Invoice, InvoiceSequence, MembershipSubscription, PaymentTransaction, SubscriptionPlan
from .notifications import send_certificate_whatsapp


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
    readonly_fields = ("slug", "created_at", "updated_at")
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
    actions = ("send_certificate_whatsapp_action",)

    @admin.action(description="Selected active memberships के certificate WhatsApp पर भेजें")
    def send_certificate_whatsapp_action(self, request, queryset):
        sent = 0
        skipped = 0
        for membership in queryset.select_related("user"):
            certificate = getattr(membership, "certificate", None)
            if membership.status != MembershipSubscription.ACTIVE or not certificate:
                skipped += 1
                continue
            sent += send_certificate_whatsapp(certificate)
        self.message_user(request, f"WhatsApp certificate send: {sent}. Skipped: {skipped}.")


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "user", "subscription", "issued_at")
    search_fields = ("certificate_number", "user__username", "user__email")
    readonly_fields = ("certificate_number", "issued_at")
    actions = ("send_certificate_whatsapp_action",)

    @admin.action(description="Selected certificates WhatsApp पर भेजें")
    def send_certificate_whatsapp_action(self, request, queryset):
        sent = 0
        for certificate in queryset.select_related("user", "subscription"):
            sent += send_certificate_whatsapp(certificate)
        self.message_user(request, f"WhatsApp certificate send: {sent}.")


@admin.register(PaymentTransaction)
class PaymentTransactionAdmin(admin.ModelAdmin):
    list_display = ("razorpay_order_id", "user_name", "plan_name", "amount_paise", "status", "gateway_status", "paid_at", "created_at")
    list_filter = ("status", "gateway_status", "currency", "created_at")
    search_fields = ("razorpay_order_id", "razorpay_payment_id", "user_name", "user_email", "user_phone")
    readonly_fields = (
        "subscription", "user_name", "user_email", "user_phone", "user_address", "plan_name",
        "amount_paise", "currency", "status", "razorpay_order_id", "razorpay_payment_id",
        "razorpay_signature", "gateway_status", "failure_reason", "gateway_response", "paid_at",
        "created_at", "updated_at",
    )


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ("invoice_number", "payment", "total_paise", "currency", "issued_at")
    search_fields = ("invoice_number", "payment__razorpay_order_id", "payment__razorpay_payment_id", "payment__user_email")
    readonly_fields = ("payment", "invoice_number", "issued_at", "description", "subtotal_paise", "tax_paise", "total_paise", "currency", "created_at")

    def has_add_permission(self, request):
        return False


@admin.register(InvoiceSequence)
class InvoiceSequenceAdmin(admin.ModelAdmin):
    list_display = ("financial_year", "next_number")
    readonly_fields = ("financial_year", "next_number")

    def has_add_permission(self, request):
        return False
