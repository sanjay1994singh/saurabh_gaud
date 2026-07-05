from django.apps import AppConfig


class SevaPrakalpConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "seva_prakalp"
    verbose_name = "Seva Prakalp"

    def ready(self):
        from dharm_raksha_sangh.media_cleanup import register_file_cleanup

        from .models import SevaPrakalp

        register_file_cleanup(SevaPrakalp, ("image",))
