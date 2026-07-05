from django.contrib import admin

from .models import Patrika


@admin.register(Patrika)
class PatrikaAdmin(admin.ModelAdmin):
    list_display = ("title", "issue_name", "published_date", "is_active", "is_featured", "display_order")
    list_filter = ("is_active", "is_featured", "published_date", "created_at")
    search_fields = ("title", "issue_name", "short_description", "description")
    readonly_fields = ("created_at", "updated_at")
    fieldsets = (
        ("Patrika Details", {"fields": ("title", "issue_name", "short_description", "description")}),
        ("Files", {"fields": ("pdf", "cover_image")}),
        ("Publishing", {"fields": ("published_date", "is_active", "is_featured", "display_order")}),
        ("System", {"fields": ("created_at", "updated_at")}),
    )

