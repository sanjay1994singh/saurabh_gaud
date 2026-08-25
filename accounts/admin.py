from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Country, State, User
from subscriptions.models import MembershipSubscription
from subscriptions.notifications import send_certificate_whatsapp


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("name", "code", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name", "code")


@admin.register(State)
class StateAdmin(admin.ModelAdmin):
    list_display = ("name", "country", "is_active")
    list_filter = ("country", "is_active")
    search_fields = ("name", "country__name")
    autocomplete_fields = ("country",)


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    fieldsets = UserAdmin.fieldsets + (
        ("सदस्य विवरण", {"fields": ("phone", "father_spouse_name", "photo", "address", "city", "district", "pin_code", "country", "state_obj")}),
    )
    list_display = UserAdmin.list_display + ("phone", "father_spouse_name", "city", "district", "pin_code", "country", "state_obj")
    autocomplete_fields = ("country", "state_obj")
    actions = ("send_active_certificates_whatsapp",)

    @admin.action(description="Selected सदस्यों के active certificates WhatsApp पर भेजें")
    def send_active_certificates_whatsapp(self, request, queryset):
        sent = 0
        skipped = 0
        memberships = (
            MembershipSubscription.objects
            .filter(user__in=queryset, status=MembershipSubscription.ACTIVE)
            .select_related("user")
        )
        for membership in memberships:
            certificate = getattr(membership, "certificate", None)
            if not certificate:
                skipped += 1
                continue
            sent += send_certificate_whatsapp(certificate)
        self.message_user(request, f"WhatsApp certificate send: {sent}. Skipped: {skipped}.")
