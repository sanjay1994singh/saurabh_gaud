from django.contrib import admin

from .models import HamareStambh


@admin.register(HamareStambh)
class HamareStambhAdmin(admin.ModelAdmin):
    list_display = ("name", "designation", "is_active", "is_featured", "display_order")
    list_filter = ("is_active", "is_featured", "created_at")
    search_fields = ("name", "designation", "short_description", "content")
    readonly_fields = ("created_at", "updated_at")
