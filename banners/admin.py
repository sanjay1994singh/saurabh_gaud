from django.contrib import admin

from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ("title", "placement", "show_everywhere", "is_active", "starts_at", "ends_at", "display_order")
    list_filter = ("placement", "show_everywhere", "is_active", "starts_at", "ends_at")
    search_fields = ("title", "text", "link_url")
    ordering = ("-created_at", "display_order")
    readonly_fields = ("created_at", "updated_at", "placement_help")
    fieldsets = (
        ("Where this banner appears", {"fields": ("placement_help", "placement", "show_everywhere", "display_order")}),
        ("Banner content", {"fields": ("title", "image", "text", "link_url", "link_label")}),
        ("Schedule", {"fields": ("is_active", "starts_at", "ends_at")}),
        ("System", {"fields": ("created_at", "updated_at")}),
    )

    def placement_help(self, obj):
        return (
            "Header top = every page below navigation, recommended 1200 x 180 px. "
            "Home after hero = homepage below hero, recommended 1200 x 250 px. "
            "Home middle = homepage before Hamare Stambh, recommended 1200 x 250 px. "
            "Footer top = every page above footer, recommended 1200 x 180 px. "
            "Sidebar = detail page side ad, recommended 300 x 250 px. "
            "Show everywhere = same banner can appear in every active banner/ad slot."
        )

    placement_help.short_description = "Placement guide"
