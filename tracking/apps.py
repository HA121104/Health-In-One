from django.apps import AppConfig


class TrackingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "tracking"

    def ready(self):
        # I import signals here so the auto-scoring runs whenever a DailyHealthEntry is saved.
        import tracking.signals  # noqa