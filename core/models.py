import abc
import datetime
import functools
import json
from typing import Any, Self

from django.contrib.auth import models as auth_models
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

import logger
from .settings import Settings


settings = Settings()


class DateKeyJSONFieldEncoder(DjangoJSONEncoder):
    def encode(self, o: Any) -> str:
        if type(list(o.keys())[0]) is str:
            string = super().encode(o)
        else:
            new_object = {self.default(key): o[key] for key in o}
            string = super().encode(new_object)
        return string


class DateKeyJsonFieldDecoder(json.JSONDecoder):
    def decode(self, s: str, *args, **kwargs) -> Any:
        o = super().decode(s, *args, **kwargs)
        new_object = {datetime.date.fromisoformat(key): o[key] for key in o}
        return new_object


class CoreModel(models.Model):
    class Meta:
        abstract = True

    settings = settings
    # todo: move logger to parsing_helper
    logger = logger.Logger(Meta.__qualname__[:-5])

    @classmethod
    def get_field_verbose_name(cls, field_name: str) -> str:
        return cls._meta.get_field(field_name).verbose_name


class ParserUser(CoreModel, auth_models.AbstractUser):
    @classmethod
    def get_admin(cls) -> Self:
        return cls.objects.get(username = cls.settings.secrets.admin_user.username)


class Parsing(CoreModel):
    date = models.DateField("Дата парсинга", auto_now_add = True)
    time = models.DateTimeField("Время парсинга", auto_now_add = True)
    user = models.ForeignKey(ParserUser, models.PROTECT)

    def __str__(self) -> str:
        return f"{super().__str__()} at {self.time}"


class Item(CoreModel):
    class Meta:
        abstract = True

    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)
    user: models.ForeignKey

    def __str__(self) -> str:
        return str(self.vendor_code)


class DynamicFieldModel(CoreModel):
    class Meta:
        abstract = True

    dynamic_fields: dict[str, dict]

    @staticmethod
    @functools.cache
    def get_dynamic_field_name(field_name: str, date_or_number: datetime.date | int) -> str:
        return f"{field_name} {date_or_number}"

    @functools.cache
    def get_dynamic_field_value(self, field_name: str, date: datetime.date) -> Any:
        field = self.dynamic_fields[field_name]
        if date in field:
            data = field[date]
        else:
            data = None
        return data

    @classmethod
    @abc.abstractmethod
    def prepare(cls) -> None:
        raise NotImplementedError()
