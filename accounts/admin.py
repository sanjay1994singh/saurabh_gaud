from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import Country, State, User


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
