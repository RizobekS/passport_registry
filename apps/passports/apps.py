from django.apps import AppConfig


class PassportsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = "apps.passports"
    verbose_name = "Паспорта"

    def ready(self):
        from . import signals  # noqa
