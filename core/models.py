import logging

from django.contrib.auth import models as auth_models
from django.db import models

import logger
from .settings import Settings


settings = Settings()


class CoreModel(models.Model):
    class Meta:
        abstract = True

    settings = settings
    logger: logging.Logger

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # todo: move logger to parsing_helper
        self.__class__.logger = logger.Logger(self.__class__.__name__)


class Parsing(CoreModel):
    date = models.DateField("Дата парсинга", auto_now_add = True)
    time = models.DateTimeField("Время парсинга", auto_now_add = True)

    def __str__(self) -> str:
        return f"{super().__str__()} at {self.time}"


class Item(CoreModel):
    class Meta:
        abstract = True

    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)

    def __str__(self) -> str:
        return str(self.vendor_code)


class ParserUser(CoreModel, auth_models.AbstractUser):
    pass
