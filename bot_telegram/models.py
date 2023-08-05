from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class BotTelegramModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class SendToUsers(BotTelegramModel):
    class Meta:
        verbose_name_plural = "Send to users"

    user = models.ForeignKey(core_models.ParserUser, models.PROTECT)
    telegram_message_id = models.PositiveIntegerField()
    sent = models.BooleanField("Отправлено", null = True)

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        self.keep_amount()

    def keep_amount(self):
        instances_to_delete = self.__class__.objects.filter(user = self.user) \
                                  .order_by("-id")[self.settings.SEND_TO_USER_KEEP_AMOUNT:]
        self.__class__.objects.filter(id__in = [x.id for x in instances_to_delete]).delete()
