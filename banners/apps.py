from django.apps import AppConfig


class BannersConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "banners"

    def ready(self):
        from dharm_raksha_sangh.media_cleanup import register_file_cleanup

        from .models import Banner

        register_file_cleanup(Banner, ("image",))
