from django.apps import AppConfig


class ProjectsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.projects'
    verbose_name = 'Projects'

    def ready(self):
        # Import signals so they are connected when the app is ready
        import apps.projects.signals  # noqa
