from django.contrib import admin

from .models import Event


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "start_date",
        "end_date",
        "recurring_month",
        "recurring_day",
        "venue",
        "is_permanent",
        "is_featured",
        "is_active",
        "display_order",
    )
    list_filter = (
        "is_active",
        "is_featured",
        "is_permanent",
        "recurring_month",
        "start_date",
        "created_at",
    )
    search_fields = ("title", "short_description", "description", "venue")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        (None, {"fields": ("title", "short_description", "description", "image", "venue")}),
        (
            "Calendar",
            {
                "fields": (
                    "start_date",
                    "end_date",
                    "start_time",
                    "is_permanent",
                    "recurring_month",
                    "recurring_day",
                )
            },
        ),
        ("Display", {"fields": ("is_featured", "is_active", "display_order")}),
        ("System", {"fields": ("created_at", "updated_at")}),
    )
