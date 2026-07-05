from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "events"

    def ready(self):
        from dharm_raksha_sangh.media_cleanup import register_file_cleanup

        from .models import Event

        register_file_cleanup(Event, ("image",))
