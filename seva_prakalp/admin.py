from django.contrib import admin

from .models import SevaPrakalp


@admin.register(SevaPrakalp)
class SevaPrakalpAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "is_featured", "start_date", "created_at")
    list_filter = ("is_active", "is_featured", "start_date", "created_at")
    search_fields = ("name", "short_description", "content", "location")
    readonly_fields = ("created_at", "updated_at")
