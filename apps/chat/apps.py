from django.apps import AppConfig


class ChatConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.chat'
    verbose_name = 'Chat Application'

    def ready(self):
        # Import signal handlers to ensure they are registered
        try:
            from . import signals  # noqa: F401
        except Exception:
            # Avoid app ready failing due to signal import errors
            pass
