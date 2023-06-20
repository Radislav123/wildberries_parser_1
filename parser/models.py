import datetime

from django.contrib.postgres.fields import ArrayField
from django.db import models


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)
    # название для сводной таблицы позиций
    name_position = models.CharField("Название товара", null = True)
    # название для сводной таблицы цен
    name_price = models.CharField("Название товара", null = True)

    def __str__(self) -> str:
        return str(self.vendor_code)


class Keyword(ProjectModel):
    """Ключевые слова, привязанные к конкретному товару."""

    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    value = models.CharField("Ключевая фраза")

    def __str__(self) -> str:
        return self.value


class Position(ProjectModel):
    """Позиция товара в поисковой выдаче по конкретному ключевому слову в определенный момент времени."""

    # noinspection PyProtectedMember
    keyword = models.ForeignKey(Keyword, models.PROTECT, verbose_name = Keyword._meta.get_field("value").verbose_name)
    city = models.CharField("Город")
    # количество товаров на страницах
    page_capacities = ArrayField(models.PositiveIntegerField(), verbose_name = "Емкости страниц", null = True)
    page = models.PositiveIntegerField("Страница", null = True)
    value = models.PositiveIntegerField("Позиция", null = True)
    parse_time = models.DateTimeField("Время парсинга", auto_now = True)
    parse_date = models.DateField("Дата парсинга", auto_now = True)

    def get_average_position_for(self, days: int) -> None | int:
        """Средняя позиция за определенное количество дней."""

        delta = datetime.timedelta(days = days)
        positions = [
            x.value for x in Position.objects.filter(
                keyword = self.keyword,
                city = self.city,
                parse_time__gte = self.parse_date,
                parse_time__lte = self.parse_date + delta
            ) if x.value is not None
        ]
        if len(positions) == 0:
            average_position = None
        else:
            average_position = round(sum(positions) / len(positions))
        return average_position

    @property
    def position_repr(self) -> str:
        page = self.page
        if page is None:
            page = "-"
        return f"{page}/{self.value}"

    @property
    def real_position(self) -> int | None:
        if self.page_capacities is not None and self.value is not None:
            real_position = sum(self.page_capacities[:self.page - 1]) + self.value
        else:
            real_position = self.value
        return real_position

    def get_last_object_by_date(self, date: datetime.date) -> "Position":
        obj = self.__class__.objects.filter(
            keyword = self.keyword,
            city = self.city,
            parse_date = date
        ).order_by("parse_time").last()
        return obj


class ShowPosition(Position):
    class Meta:
        proxy = True


class Price(ProjectModel):
    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    reviews_amount = models.PositiveIntegerField("Количество отзывов", null = True)
    price = models.DecimalField("Цена до СПП", max_digits = 15, decimal_places = 2, null = True)
    final_price = models.DecimalField("Финальная цена", max_digits = 15, decimal_places = 2, null = True)
    # скидка постоянного покупателя
    personal_sale = models.PositiveIntegerField("СПП", null = True)
    parse_time = models.DateTimeField("Время парсинга", auto_now = True)
    parse_date = models.DateField("Дата парсинга", auto_now = True)

    def __str__(self) -> str:
        return str(self.item.vendor_code)

    def get_last_object_by_date(self, date: datetime.date) -> "Price":
        obj = self.__class__.objects.filter(
            item = self.item,
            parse_date = date
        ).order_by("parse_time").last()
        return obj


class ShowPrice(Price):
    class Meta:
        proxy = True


class DateComment(ProjectModel):
    text = models.TextField()
    date = models.DateField()
