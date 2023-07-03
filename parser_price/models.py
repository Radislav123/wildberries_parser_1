import datetime
from typing import Self

from django.db import models

from core import models as core_models


class ParserPriceModel(core_models.CoreModel):
    class Meta:
        abstract = True


class DateComment(ParserPriceModel):
    text = models.TextField()
    date = models.DateField()


class Category(ParserPriceModel):
    name = models.CharField("Предмет")


class Item(ParserPriceModel, core_models.Item):
    category = models.ForeignKey(Category, models.PROTECT)
    name = models.CharField("Название товара")


class Price(ParserPriceModel):
    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    parsing = models.ForeignKey(core_models.Parsing, models.PROTECT)
    reviews_amount = models.PositiveIntegerField("Количество отзывов", null = True)
    price = models.DecimalField("Цена до СПП", max_digits = 15, decimal_places = 2, null = True)
    final_price = models.DecimalField("Финальная цена", max_digits = 15, decimal_places = 2, null = True)
    personal_sale = models.PositiveIntegerField("СПП", null = True)

    def __str__(self) -> str:
        return str(self.item.vendor_code)

    def get_last_object_by_date(self, date: datetime.date) -> Self:
        obj = self.__class__.objects.filter(
            item = self.item,
            parsing__date = date
        ).order_by("parsing__time").last()
        return obj
