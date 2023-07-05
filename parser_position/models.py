import datetime
from typing import Self

from django.contrib.postgres.fields import ArrayField
from django.db import models

from core import models as core_models
from .settings import Settings


settings = Settings()


class ParserPositionModel(core_models.CoreModel):
    class Meta:
        abstract = True

    settings = settings


class Item(ParserPositionModel, core_models.Item):
    pass


class Keyword(ParserPositionModel):
    """Ключевая фраза, привязанная к конкретному товару."""

    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    item_name = models.CharField("Название")
    value = models.CharField("Ключевая фраза")

    def __str__(self) -> str:
        return self.value


class Position(ParserPositionModel):
    """Позиция товара в поисковой выдаче по конкретной ключевой фразе в определенный момент времени."""

    # noinspection PyProtectedMember
    keyword = models.ForeignKey(Keyword, models.PROTECT, verbose_name = Keyword._meta.get_field("value").verbose_name)
    parsing = models.ForeignKey(core_models.Parsing, models.PROTECT)
    city = models.CharField("Город")
    # количества товаров на страницах
    page_capacities = ArrayField(models.PositiveIntegerField(), verbose_name = "Емкости страниц", null = True)
    page = models.PositiveIntegerField("Страница", null = True)
    value = models.PositiveIntegerField("Позиция", null = True)

    @property
    def position_repr(self) -> str:
        page = self.page
        if page is None:
            page = "-"
        return f"{page}/{self.value}"

    @property
    def real_position(self) -> int | None:
        """Позиция с учетом страницы."""
        # 5 страница, все страницы с заполненностью по 100, 30 позиция
        # 100 * (5 - 1) + 30 = 430

        if self.page_capacities is not None and self.value is not None:
            real_position = sum(self.page_capacities[:self.page - 1]) + self.value
        else:
            real_position = self.value
        return real_position

    # todo: remove method?
    def get_last_object_by_date(self, date: datetime.date) -> Self:
        obj = self.__class__.objects.filter(
            keyword = self.keyword,
            city = self.city,
            parsing__date = date
        ).order_by("parsing__time").last()
        return obj
