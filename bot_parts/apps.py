from django.apps import AppConfig


class BotPartsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "bot_parts"

    def ready(self) -> None:
        from . import signals  # noqa
        return super().ready()
