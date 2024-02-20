import abc
import datetime
import functools
import json
import traceback
from typing import Any, Self, TYPE_CHECKING

from django.contrib.auth import models as auth_models
from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

import logger
from .settings import Settings


if TYPE_CHECKING:
    from bot_telegram.bot import Subscriptions

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
            obj = self.dump_exception(value)
        elif isinstance(value, dict):
            obj = value
        else:
            obj = {super().default(value): ""}
        return obj

    @staticmethod
    def dump_exception(exception: BaseException) -> dict:
        tb = []
        for i in traceback.format_exception(exception):
            tb.extend(i.split('\n'))

        # noinspection PyUnresolvedReferences
        obj = {
            "class": str(type(exception)),
            "message": str(exception),
            "args": exception.args,
            "cause": exception.__cause__,
            "traceback": tb
        }
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
    seller_api_token = models.CharField("Токен продавца", null = True)
    subscribed = models.BooleanField("Активность подписок")
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

    def get_default_username(self) -> str:
        return f"user_{self.id}"

    def update_subscriptions_info(self, not_subscribed: "Subscriptions") -> None:
        subscribed = len(not_subscribed) == 0
        if self.subscribed != subscribed:
            self.subscribed = subscribed
            self.save()

    def save(self, *args, **kwargs) -> None:
        super().save(*args, **kwargs)
        if self.username == "" or self.username is None:
            self.username = self.get_default_username()
        # для сохранения username с выданным id (не None)
        super().save()


# todo: объединить параллельные парсинги в один
class Parsing(CoreModel):
    date = models.DateField("Дата начала парсинга", auto_now_add = True)
    time = models.DateTimeField("Время начала парсинга", auto_now_add = True)
    duration = models.DurationField("Продолжительность парсинга")
    # None - парсинг не закончен
    # True - без ошибок
    # False - с ошибками
    success = models.BooleanField(null = True)
    # {item: error}
    not_parsed_items = models.JSONField(
        encoder = NotParsedItemsJsonFieldEncoder,
        null = True
    )
    type = models.CharField(null = True)

    def __str__(self) -> str:
        return f"{super().__str__()} at {self.time}"

    def save(self, force_insert = False, force_update = False, using = None, update_fields = None) -> None:
        if self.time is None:
            time = datetime.datetime.now()
        else:
            time = self.time
        self.duration = datetime.datetime.now() - time
        super().save(force_insert, force_update, using, update_fields)


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
