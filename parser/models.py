import datetime

from django.db import models


class ProjectModel(models.Model):
    class Meta:
        abstract = True


class Item(ProjectModel):
    vendor_code = models.PositiveIntegerField("Артикул", primary_key = True)
    name = models.CharField("Название товара", null = True)

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
    value = models.IntegerField("Позиция в выдаче", null = True)
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
    def day_position(self) -> None | int:
        """Средняя позиция за день, когда выполнялся парсинг данной позиции."""

        return self.get_average_position_for(1)

    @property
    def month_position(self) -> None | int:
        """Средняя позиция за 30 дней предшествующих дню, когда выполнялся парсинг данной позиции."""

        return self.get_average_position_for(30)


class ShowPosition(Position):
    class Meta:
        proxy = True


class Price(ProjectModel):
    item = models.ForeignKey(Item, models.PROTECT, verbose_name = "Товар")
    price = models.DecimalField("Цена до СПП", max_digits = 15, decimal_places = 2)
    final_price = models.DecimalField("Финальная цена", max_digits = 15, decimal_places = 2)
    # скидка постоянного покупателя
    personal_sale = models.IntegerField("СПП")
    parse_time = models.DateTimeField("Время парсинга", auto_now = True)
    parse_date = models.DateField("Дата парсинга", auto_now = True)

    def __str__(self) -> str:
        return str(self.item.vendor_code)


class ShowPrice(Price):
    class Meta:
        proxy = True
