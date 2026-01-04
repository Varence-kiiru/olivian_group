from django.apps import AppConfig
import threading
import time


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core'

    def ready(self):
        """Import signals when the app is ready"""
        import apps.core.signals

        from .tasks import log_system_metrics

        def run_metrics_logger():
            while True:
                log_system_metrics()
                time.sleep(60)  # Run every minute

        # Start metrics logging in a separate thread
        if not threading.current_thread().name == 'MainThread':
            metrics_thread = threading.Thread(target=run_metrics_logger, daemon=True)
            metrics_thread.start()
