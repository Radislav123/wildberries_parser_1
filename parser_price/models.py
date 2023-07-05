import datetime
import json
from typing import Any, Self

from django.core.serializers.json import DjangoJSONEncoder
from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class ParserPriceModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class DateComment(ParserPriceModel):
    text = models.TextField()
    date = models.DateField()


class Category(ParserPriceModel):
    class Meta:
        verbose_name_plural = "Categories"

    name = models.CharField("Предмет")

    def __str__(self) -> str:
        return str(self.name)


class Item(ParserPriceModel, core_models.Item):
    name = models.CharField("Название")
    # noinspection PyProtectedMember
    category = models.ForeignKey(
        Category,
        models.PROTECT,
        verbose_name = Category._meta.get_field("name").verbose_name,
        null = True
    )


class Price(ParserPriceModel):
    # noinspection PyProtectedMember
    item = models.ForeignKey(Item, models.PROTECT, verbose_name = Item._meta.get_field("vendor_code").verbose_name)
    parsing = models.ForeignKey(core_models.Parsing, models.PROTECT)
    reviews_amount = models.PositiveIntegerField("Количество отзывов")
    price = models.FloatField("Цена до СПП", null = True)
    final_price = models.FloatField("Финальная цена", null = True)
    personal_sale = models.PositiveIntegerField("СПП", null = True)

    # todo: remove method?
    def get_last_object_by_date(self, date: datetime.date) -> Self:
        obj = self.__class__.objects.filter(
            item = self.item,
            parsing__date = date
        ).order_by("parsing__time").last()
        return obj

    @classmethod
    def get_last_by_item_date(cls, item: Item, date: datetime.date) -> Self:
        obj = cls.objects.filter(
            item = item,
            parsing__date = date
        ).order_by("parsing__time").last()
        return obj


# todo: move it to core
class DateKeyJSONFieldEncoder(DjangoJSONEncoder):
    def encode(self, o: Any) -> str:
        if type(list(o.keys())[0]) is str:
            string = super().encode(o)
        else:
            new_object = {self.default(key): o[key] for key in o}
            string = super().encode(new_object)
        return string


# todo: move it to core
class DateKeyJsonFieldDecoder(json.JSONDecoder):
    def decode(self, s: str, *args, **kwargs) -> Any:
        o = super().decode(s, *args, **kwargs)
        new_object = {datetime.date.fromisoformat(key): o[key] for key in o}
        return new_object


class PreparedPrice(ParserPriceModel):
    """Таблица для отображения необходимой пользователю информации."""

    price = models.ForeignKey(Price, models.PROTECT)
    # {date: value}
    prices = models.JSONField(encoder = DateKeyJSONFieldEncoder, decoder = DateKeyJsonFieldDecoder)
    final_prices = models.JSONField(encoder = DateKeyJSONFieldEncoder, decoder = DateKeyJsonFieldDecoder)
    personal_sales = models.JSONField(encoder = DateKeyJSONFieldEncoder, decoder = DateKeyJsonFieldDecoder)

    @classmethod
    def prepare_prices(cls) -> None:
        cls.objects.all().delete()
        new_objects = [
            cls(
                price = Price.objects.filter(item = item).order_by("parsing__time").last()
            ) for item in Item.objects.all()
        ]

        today = datetime.date.today()
        date_range = [today - datetime.timedelta(x) for x in range(cls.settings.MAX_HISTORY_DEPTH)]
        for obj in new_objects:
            obj.prices = {}
            obj.final_prices = {}
            obj.personal_sales = {}
            for date in date_range:
                last_price = Price.get_last_by_item_date(obj.price.item, date)
                if last_price is not None:
                    obj.prices[date] = last_price.price
                    obj.final_prices[date] = last_price.final_price
                    obj.personal_sales[date] = last_price.personal_sale
                else:
                    obj.prices[date] = None
                    obj.final_prices[date] = None
                    obj.personal_sales[date] = None
            obj.save()
