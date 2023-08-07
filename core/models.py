import abc
import datetime
import functools
import json
import traceback
from typing import Any, Self

from django.contrib.auth import models as auth_models
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

import logger
from .settings import Settings


settings = Settings()


class DateKeyJSONFieldEncoder(DjangoJSONEncoder):
    def encode(self, o: Any) -> str:
        if len(o) > 0 and type(list(o.keys())[0]) is str:
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


class NotParsedItemsJsonFieldEncoder(DjangoJSONEncoder):
    def dump_value(self, value) -> dict:
        if isinstance(value, BaseException):
            tb = []
            for i in traceback.format_exception(value):
                tb.extend(i.split('\n'))

            # noinspection PyUnresolvedReferences
            obj = {
                "class": str(type(value)),
                "message": value.msg,
                "args": value.args,
                "cause": value.__cause__,
                "traceback": tb
            }
        elif isinstance(value, dict):
            obj = value
        else:
            obj = {super().default(value): ""}
        return obj

    def encode(self, o: Any) -> str:
        new_object = {str(key): self.dump_value(o[key]) for key in o}
        string = json.dumps(new_object, indent = 2)
        return string


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
    telegram_user_id = models.BigIntegerField("Telegram user_id", null = True)
    telegram_chat_id = models.BigIntegerField("Telegram chat_id", null = True)
    _customer: "ParserUser" = None
    _developer: "ParserUser" = None

    @classmethod
    def get_customer(cls) -> Self:
        if cls._customer is None:
            cls._customer = cls.objects.get(username = cls.settings.secrets.customer_user.username)
        return cls._customer

    @classmethod
    def get_developer(cls) -> Self:
        if cls._developer is None:
            cls._developer = cls.objects.get(username = cls.settings.secrets.developer_user.username)
        return cls._developer


class Parsing(CoreModel):
    date = models.DateField("Дата парсинга", auto_now_add = True)
    time = models.DateTimeField("Время парсинга", auto_now_add = True)
    # None - парсинг не закончен
    # True - без ошибок
    # False - с ошибками
    success = models.BooleanField(null = True)
    # {item: error}
    not_parsed_items = models.JSONField(
        encoder = NotParsedItemsJsonFieldEncoder,
        null = True
    )

    def __str__(self) -> str:
        return f"{super().__str__()} at {self.time}"


class Item(CoreModel):
    class Meta:
        abstract = True

    vendor_code = models.PositiveIntegerField("Артикул")
    user: models.ForeignKey

    def __str__(self) -> str:
        return str(self.vendor_code)

    @property
    def link(self) -> str:
        return f'https://www.wildberries.ru/catalog/{self.vendor_code}/detail.aspx'


class DynamicFieldModel(CoreModel):
    class Meta:
        abstract = True

    dynamic_fields: dict[str, dict]

    @staticmethod
    @functools.cache
    def get_dynamic_field_name(field_name: str, date_or_number: datetime.date | int) -> str:
        return f"{field_name} {date_or_number}".strip()

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
    def prepare(cls, *args, **kwargs) -> None:
        raise NotImplementedError()
