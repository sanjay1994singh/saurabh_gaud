from django.apps import AppConfig


class HamareStambhConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "hamare_stambh"
    verbose_name = "Hamare Stambh"

    def ready(self):
        from dharm_raksha_sangh.media_cleanup import register_file_cleanup

        from .models import HamareStambh

        register_file_cleanup(HamareStambh, ("image",))
