from django.contrib.auth import models as auth_models
from django.db import models

import logger
from .settings import Settings


settings = Settings()


class CoreModel(models.Model):
    class Meta:
        abstract = True

    settings = settings
    # todo: move logger to parsing_helper
    logger = logger.Logger(Meta.__qualname__[:-5])

    @classmethod
    def get_field_verbose_name(cls, field_name: str) -> str:
        return cls._meta.get_field(field_name).verbose_name


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
