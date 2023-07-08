from core import models as core_models
from .settings import Settings


settings = Settings()


class BotTelegramModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings
