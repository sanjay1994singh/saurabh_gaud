from django.contrib import admin

from .models import Patrika, PatrikaPage
from .services import convert_patrika_pdf_to_pages


class PatrikaPageInline(admin.TabularInline):
    model = PatrikaPage
    extra = 0
    readonly_fields = ("number", "image", "created_at")
    fields = ("number", "image", "created_at")
    can_delete = False


@admin.register(Patrika)
class PatrikaAdmin(admin.ModelAdmin):
    list_display = ("title", "issue_name", "published_date", "page_count", "is_active", "is_featured", "display_order")
    list_filter = ("is_active", "is_featured", "published_date", "created_at")
    search_fields = ("title", "issue_name", "short_description", "description")
    readonly_fields = ("created_at", "updated_at")
    inlines = (PatrikaPageInline,)
    actions = ("regenerate_pages",)
    fieldsets = (
        ("Patrika Details", {"fields": ("title", "issue_name", "short_description", "description")}),
        ("Files", {"fields": ("pdf", "cover_image")}),
        ("Publishing", {"fields": ("published_date", "is_active", "is_featured", "display_order")}),
        ("System", {"fields": ("created_at", "updated_at")}),
    )

    def save_model(self, request, obj, form, change):
        pdf_changed = not change or "pdf" in form.changed_data
        super().save_model(request, obj, form, change)

        if pdf_changed:
            try:
                page_count = convert_patrika_pdf_to_pages(obj)
            except Exception as error:
                self.message_user(
                    request,
                    f"PDF saved, but page images could not be created: {error}",
                    level="ERROR",
                )
            else:
                self.message_user(request, f"PDF converted successfully. {page_count} page(s) created.")

    @admin.action(description="Regenerate page images for selected patrika PDFs")
    def regenerate_pages(self, request, queryset):
        converted = 0
        for patrika in queryset:
            try:
                convert_patrika_pdf_to_pages(patrika)
            except Exception as error:
                self.message_user(
                    request,
                    f"{patrika} could not be converted: {error}",
                    level="ERROR",
                )
            else:
                converted += 1
        if converted:
            self.message_user(request, f"{converted} patrika PDF(s) converted into page images.")


@admin.register(PatrikaPage)
class PatrikaPageAdmin(admin.ModelAdmin):
    list_display = ("patrika", "number", "created_at")
    list_filter = ("created_at",)
    search_fields = ("patrika__title", "patrika__issue_name")
