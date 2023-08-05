from core import models as core_models
from .settings import Settings

from django.db import models

settings = Settings()


class BotTelegramModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


# todo: добавить логику, удаляющую старые сообщения/рассылки
class SendToUsers(BotTelegramModel):
    class Meta:
        verbose_name_plural = "Send to users"

    user = models.ForeignKey(core_models.ParserUser, models.PROTECT)
    telegram_message_id = models.PositiveIntegerField()
    sent = models.BooleanField("Отправлено", null = True)
